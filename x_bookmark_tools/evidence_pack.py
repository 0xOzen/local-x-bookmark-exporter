#!/usr/bin/env python3
"""Create deterministic Markdown evidence packs from validated local exports."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from x_bookmark_tools.archive_doctor import build_receipt, deterministic_json, validate_export_file

TOOL_NAME = "x-bookmark-evidence-pack"
MANIFEST_VERSION = 1
SLUG_RE = re.compile(r"[^a-z0-9]+")
TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


@dataclass(frozen=True)
class EvidencePackResult:
    output_dir: Path
    manifest: dict[str, Any]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def slugify(value: str, fallback: str = "bookmark", limit: int = 72) -> str:
    normalized = SLUG_RE.sub("-", value.lower()).strip("-")
    normalized = re.sub(r"-+", "-", normalized)
    if not normalized:
        normalized = fallback
    return normalized[:limit].strip("-") or fallback


def date_prefix(timestamp: str) -> str:
    return timestamp[:10] if isinstance(timestamp, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", timestamp) else "undated"


def normalize_tags(tags: list[str] | None) -> list[str]:
    normalized = sorted(set(tags or []))
    for tag in normalized:
        if not isinstance(tag, str) or not TAG_RE.fullmatch(tag):
            raise ValueError(
                "tag must match grammar: 1-64 chars; ASCII alphanumeric start; "
                "then ASCII alphanumeric, dot, underscore, or hyphen only"
            )
    return normalized


def ensure_output_path_is_new(output_dir: Path) -> None:
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError(f"output path already exists; choose a new directory path: {output_dir}")


def unique_note_name(record: dict[str, Any], used: set[str]) -> str:
    text_slug = slugify(str(record.get("text", "")), limit=64)
    base = "-".join(
        [
            date_prefix(str(record.get("postedAt", ""))),
            slugify(str(record.get("authorHandle", "unknown")), "unknown", 24),
            str(record.get("id", "unknown")),
            text_slug,
        ]
    )
    candidate = f"{base}.md"
    counter = 2
    while candidate in used:
        candidate = f"{base}-{counter}.md"
        counter += 1
    used.add(candidate)
    return candidate


def markdown_escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=False)


def frontmatter_string(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def safe_write(base_dir: Path, relative: str, content: str) -> Path:
    base_resolved = base_dir.resolve()
    target = (base_dir / relative).resolve()
    try:
        target.relative_to(base_resolved)
    except ValueError as error:
        raise ValueError(f"refusing to write outside output directory: {relative}") from error
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")
    return target


def note_markdown(record: dict[str, Any], export_sha256: str, tags: list[str]) -> str:
    title = f"@{record['authorHandle']} - {record['id']}"
    media = record.get("mediaUrls", [])
    lines = [
        "---",
        f"title: {frontmatter_string(title)}",
        f"x_bookmark_id: {frontmatter_string(record['id'])}",
        f"source_url: {frontmatter_string(record['url'])}",
        f"author_handle: {frontmatter_string(record['authorHandle'])}",
        f"author_name: {frontmatter_string(record['authorName'])}",
        f"posted_at: {frontmatter_string(record['postedAt'])}",
        f"captured_at: {frontmatter_string(record['capturedAt'])}",
        f"language: {frontmatter_string(record['language'])}",
        f"export_sha256: {frontmatter_string(export_sha256)}",
        f"tags: {frontmatter_string(tags)}",
        "---",
        "",
        f"# {markdown_escape(title)}",
        "",
        "## Provenance",
        "",
        f"- Source URL: <{record['url']}>",
        f"- Author: {markdown_escape(record['authorName'])} (@{markdown_escape(record['authorHandle'])})",
        f"- Posted at: `{record['postedAt']}`",
        f"- Captured by exporter at: `{record['capturedAt']}`",
        f"- Export SHA-256: `{export_sha256}`",
        "- Completeness: best-effort export metadata only; this note does not claim the bookmark archive is complete.",
        "",
        "## Original text",
        "",
        markdown_escape(record.get("text", "")) or "_No visible text recorded._",
        "",
        "## Media URLs",
        "",
    ]
    if media:
        lines.extend(f"- <{url}>" for url in media)
    else:
        lines.append("- None recorded")
    return "\n".join(lines) + "\n"


def index_markdown(payload: dict[str, Any], receipt: dict[str, Any], note_entries: list[dict[str, Any]], tags: list[str]) -> str:
    meta = payload["meta"]
    lines = [
        "# X Bookmark Evidence Pack",
        "",
        "Deterministic Markdown index for a local X Bookmark Exporter JSON file.",
        "It is Obsidian-compatible plain Markdown and does not call X, AI services, or a browser.",
        "",
        "## Source provenance",
        "",
        f"- Source file: `{receipt['source_file']}`",
        f"- Export SHA-256: `{receipt['input_sha256']}`",
        f"- Schema version: `{receipt['schemaVersion']}`",
        f"- Claimed count: {receipt['claimed_count']}",
        f"- Note count: {len(note_entries)}",
        f"- Stop reason: `{meta.get('stopReason')}`",
        f"- Best-effort export: {meta.get('completeness')}",
        f"- Tags: {', '.join(tags) if tags else 'None'}",
        "",
        "## Bookmarks",
        "",
        "| Date | Author | Note | Source |",
        "| --- | --- | --- | --- |",
    ]
    for entry in note_entries:
        record = entry["record"]
        note_path = entry["path"]
        lines.append(
            "| "
            f"{markdown_escape(record['postedAt'])} | "
            f"@{markdown_escape(record['authorHandle'])} | "
            f"[{markdown_escape(record['id'])}]({note_path}) | "
            f"[Open post]({record['url']}) |"
        )
    lines.extend([
        "",
        "## Safety notes",
        "",
        "- Uses only local files generated from a valid local JSON export.",
        "- Does not mutate the input export.",
        "- Does not infer or claim completeness beyond exporter metadata.",
        "- Public examples are fictional fixtures, not real bookmark data.",
    ])
    return "\n".join(lines) + "\n"


def build_evidence_pack(input_path: Path, output_dir: Path, tags: list[str] | None = None) -> EvidencePackResult:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    tags = normalize_tags(tags)
    validation = validate_export_file(input_path)
    if not validation.valid:
        raise ValueError("valid local JSON export required before building an evidence pack")
    payload = validation.payload
    assert payload is not None
    receipt = build_receipt(input_path)
    export_sha256 = receipt["input_sha256"]

    ensure_output_path_is_new(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)

    used_names: set[str] = set()
    note_entries: list[dict[str, Any]] = []
    for record in payload["bookmarks"]:
        filename = unique_note_name(record, used_names)
        relative = f"bookmarks/{filename}"
        note_path = safe_write(output_dir, relative, note_markdown(record, export_sha256, tags))
        note_entries.append({"path": relative, "record": record, "sha256": sha256_file(note_path), "bytes": note_path.stat().st_size})

    index_path = safe_write(output_dir, "index.md", index_markdown(payload, receipt, note_entries, tags))
    files = [
        {
            "path": "index.md",
            "sha256": sha256_file(index_path),
            "bytes": index_path.stat().st_size,
        }
    ]
    files.extend(
        {"path": entry["path"], "sha256": entry["sha256"], "bytes": entry["bytes"]}
        for entry in note_entries
    )
    manifest = {
        "tool": TOOL_NAME,
        "manifestVersion": MANIFEST_VERSION,
        "source": {
            "source_file": receipt["source_file"],
            "export_sha256": export_sha256,
            "schemaVersion": receipt["schemaVersion"],
            "claimed_count": receipt["claimed_count"],
            "bookmark_count": receipt["bookmark_count"],
            "stop_reason": receipt["stop_reason"],
            "completeness": receipt["completeness"],
        },
        "tags": tags,
        "files": sorted(files, key=lambda item: item["path"]),
    }
    safe_write(output_dir, "manifest.json", deterministic_json(manifest))
    return EvidencePackResult(output_dir=output_dir, manifest=manifest)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="x-bookmark-evidence-pack",
        description="Create a deterministic Markdown evidence pack from a valid local X bookmark JSON export.",
    )
    parser.add_argument("input", type=Path, help="Local JSON export produced by Local X Bookmark Exporter")
    parser.add_argument("output_dir", type=Path, help="New directory to create with the Markdown pack; refuses existing paths")
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="Optional tag matching [A-Za-z0-9][A-Za-z0-9._-]{0,63}; repeatable",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        result = build_evidence_pack(args.input, args.output_dir, tags=args.tag)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(deterministic_json(result.manifest), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
