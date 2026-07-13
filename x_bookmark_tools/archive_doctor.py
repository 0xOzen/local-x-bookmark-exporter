#!/usr/bin/env python3
"""Validate Local X Bookmark Exporter JSON archives and write receipts.

The implementation is deliberately standard-library only and local-only. It reads
one JSON file, never calls X, never opens a browser, and never mutates input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

TOOL_NAME = "x-bookmark-archive-doctor"
RECEIPT_VERSION = 1
SUPPORTED_SCHEMA_VERSION = 1
REQUIRED_META_FIELDS = {
    "schemaVersion",
    "sourcePage",
    "method",
    "completeness",
    "startedAt",
    "exportedAt",
    "count",
    "stopReason",
    "options",
}
REQUIRED_BOOKMARK_FIELDS = {
    "id",
    "url",
    "authorHandle",
    "authorName",
    "postedAt",
    "text",
    "language",
    "mediaUrls",
    "capturedAt",
}
HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{1,15}$")
ID_RE = re.compile(r"^\d{1,30}$")
LANGUAGE_RE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?$|^und$")
HOSTILE_PATTERNS = [
    (re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]"), "control character"),
    (re.compile(r"<\s*/?\s*script\b", re.IGNORECASE), "script tag"),
    (re.compile(r"javascript\s*:", re.IGNORECASE), "javascript URL"),
    (re.compile(r"data\s*:\s*text/html", re.IGNORECASE), "HTML data URL"),
    (re.compile(r"file\s*:", re.IGNORECASE), "local file URL"),
    (re.compile(r"(?:^|[/\\])\.\.(?:[/\\]|$)"), "path traversal sequence"),
]


def is_allowed_source_page(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.fragment:
        return False
    if parsed.username or parsed.password:
        return False
    try:
        port = parsed.port
    except ValueError:
        return False
    if port not in (None, 443):
        return False
    if parsed.hostname not in {"x.com", "www.x.com"}:
        return False
    return parsed.path == "/i/bookmarks" or parsed.path.startswith("/i/bookmarks/")


@dataclass(frozen=True)
class ValidationResult:
    payload: dict[str, Any] | None
    errors: list[str]
    warnings: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors and self.payload is not None


def read_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as error:
        return None, [f"input is not UTF-8 JSON: {error}"]
    except json.JSONDecodeError as error:
        return None, [f"input is not valid JSON: line {error.lineno} column {error.colno}: {error.msg}"]
    if not isinstance(value, dict):
        return None, ["top-level JSON value must be an object"]
    return value, []


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_export_timestamp(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value:
        errors.append(f"{field} must be a non-empty ISO-8601 UTC string")
        return
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        errors.append(f"{field} must be an ISO-8601 UTC timestamp")
        return
    if parsed.tzinfo is None or not value.endswith("Z"):
        errors.append(f"{field} must end with Z and include UTC timezone")


def find_hostile_strings(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, str):
        for pattern, label in HOSTILE_PATTERNS:
            if pattern.search(value):
                errors.append(f"hostile string in {path}: {label}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            find_hostile_strings(item, f"{path}[{index}]", errors)
    elif isinstance(value, dict):
        for key, item in value.items():
            find_hostile_strings(item, f"{path}.{key}", errors)


def validate_status_url(value: Any, bookmark_id: str, handle: str, field: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{field} must be a string")
        return
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.netloc != "x.com" or parsed.query or parsed.fragment:
        errors.append(f"{field} must be a canonical https://x.com/<handle>/status/<id> URL")
        return
    match = re.fullmatch(r"/([^/]+)/status/(\d+)", parsed.path)
    if not match:
        errors.append(f"{field} must be a canonical https://x.com/<handle>/status/<id> URL")
        return
    url_handle, url_id = match.groups()
    if url_id != bookmark_id:
        errors.append(f"{field} status id does not match bookmark id")
    if url_handle != handle:
        errors.append(f"{field} handle does not match authorHandle")


def validate_media_url(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{field} must be a string")
        return
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.fragment:
        errors.append(f"{field} must be an HTTPS media URL without a fragment")
        return
    host = parsed.netloc.lower()
    if not (host == "pbs.twimg.com" or host == "video.twimg.com" or host.endswith(".twimg.com")):
        errors.append(f"{field} must use a known rendered X media host")


def validate_payload(payload: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    find_hostile_strings(payload, "$", errors)

    meta = payload.get("meta")
    bookmarks = payload.get("bookmarks")
    if not isinstance(meta, dict):
        errors.append("meta must be an object")
        meta = {}
    if not isinstance(bookmarks, list):
        errors.append("bookmarks must be a list")
        bookmarks = []

    missing_meta = sorted(REQUIRED_META_FIELDS - set(meta))
    for field in missing_meta:
        errors.append(f"meta.{field} is required")

    schema_version = meta.get("schemaVersion")
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        errors.append(f"unsupported schemaVersion: {schema_version!r}; supported: {SUPPORTED_SCHEMA_VERSION}")

    source_page = meta.get("sourcePage")
    if not is_allowed_source_page(source_page):
        errors.append("meta.sourcePage must be an HTTPS X bookmarks route")

    if meta.get("method") != "local DOM scrolling":
        errors.append("meta.method must be 'local DOM scrolling'")

    completeness = meta.get("completeness")
    if not isinstance(completeness, str) or "best-effort" not in completeness.lower():
        errors.append("meta.completeness must preserve best-effort wording")

    for field in ("startedAt", "exportedAt"):
        parse_export_timestamp(meta.get(field), f"meta.{field}", errors)

    count = meta.get("count")
    if not isinstance(count, int) or count < 0:
        errors.append("meta.count must be a non-negative integer")
    elif count != len(bookmarks):
        errors.append(f"meta.count does not match bookmarks length: {count} != {len(bookmarks)}")

    options = meta.get("options")
    if not isinstance(options, dict):
        errors.append("meta.options must be an object")
    elif options.get("format") != "json":
        errors.append("meta.options.format must be json for companion tools")

    seen_ids: set[str] = set()
    for index, record in enumerate(bookmarks):
        prefix = f"bookmarks[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in sorted(REQUIRED_BOOKMARK_FIELDS - set(record)):
            errors.append(f"{prefix}.{field} is required")

        bookmark_id = record.get("id")
        handle = record.get("authorHandle")
        if not isinstance(bookmark_id, str) or not ID_RE.fullmatch(bookmark_id):
            errors.append(f"{prefix}.id must be a decimal string")
            bookmark_id = ""
        elif bookmark_id in seen_ids:
            errors.append(f"duplicate bookmark id: {bookmark_id}")
        else:
            seen_ids.add(bookmark_id)

        if not isinstance(handle, str) or not HANDLE_RE.fullmatch(handle):
            errors.append(f"{prefix}.authorHandle must be an X handle")
            handle = ""

        validate_status_url(record.get("url"), bookmark_id, handle, f"{prefix}.url", errors)
        for field in ("authorName", "text"):
            if not isinstance(record.get(field), str):
                errors.append(f"{prefix}.{field} must be a string")
        language = record.get("language")
        if not isinstance(language, str) or not LANGUAGE_RE.fullmatch(language):
            errors.append(f"{prefix}.language must be a BCP-47-like language code or und")
        for field in ("postedAt", "capturedAt"):
            parse_export_timestamp(record.get(field), f"{prefix}.{field}", errors)
        media_urls = record.get("mediaUrls")
        if not isinstance(media_urls, list):
            errors.append(f"{prefix}.mediaUrls must be a list")
        else:
            for media_index, media_url in enumerate(media_urls):
                validate_media_url(media_url, f"{prefix}.mediaUrls[{media_index}]", errors)

    if not bookmarks:
        warnings.append("export contains zero bookmarks; this can be valid for an empty or stopped run")
    return ValidationResult(payload=payload, errors=errors, warnings=warnings)


def validate_export_file(path: Path) -> ValidationResult:
    payload, read_errors = read_json(path)
    if read_errors:
        return ValidationResult(payload=None, errors=read_errors, warnings=[])
    assert payload is not None
    return validate_payload(payload)


def build_receipt(input_path: Path) -> dict[str, Any]:
    input_path = Path(input_path)
    result = validate_export_file(input_path)
    meta = result.payload.get("meta", {}) if result.payload else {}
    bookmarks = result.payload.get("bookmarks", []) if result.payload else []
    if not isinstance(meta, dict):
        meta = {}
    if not isinstance(bookmarks, list):
        bookmarks = []
    return {
        "tool": TOOL_NAME,
        "receiptVersion": RECEIPT_VERSION,
        "source_file": input_path.name,
        "input_sha256": sha256_file(input_path),
        "valid": result.valid,
        "schemaVersion": meta.get("schemaVersion"),
        "claimed_count": meta.get("count"),
        "bookmark_count": len(bookmarks),
        "stop_reason": meta.get("stopReason"),
        "completeness": meta.get("completeness"),
        "warnings": result.warnings,
        "errors": result.errors,
    }


def deterministic_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def receipt_to_markdown(receipt: dict[str, Any]) -> str:
    lines = [
        "# X Bookmark Archive Doctor Receipt",
        "",
        f"- Tool: `{receipt['tool']}`",
        f"- Receipt version: {receipt['receiptVersion']}",
        f"- Source file: `{receipt['source_file']}`",
        f"- Input SHA-256: `{receipt['input_sha256']}`",
        f"- Valid: `{str(receipt['valid']).lower()}`",
        f"- Claimed count: {receipt.get('claimed_count')}",
        f"- Observed bookmark records: {receipt['bookmark_count']}",
        f"- Stop reason: `{receipt.get('stop_reason')}`",
        "- Completeness: Never claims completeness; reports only the exporter's best-effort metadata.",
        "",
        "## Exporter completeness metadata",
        "",
        str(receipt.get("completeness") or "Not recorded."),
        "",
        "## Warnings",
        "",
    ]
    warnings = receipt.get("warnings") or []
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- None")
    lines.extend(["", "## Errors", ""])
    errors = receipt.get("errors") or []
    lines.extend(f"- {error}" for error in errors) if errors else lines.append("- None")
    return "\n".join(lines) + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="x-bookmark-archive-doctor",
        description="Validate a local X Bookmark Exporter JSON file and write deterministic receipts.",
    )
    parser.add_argument("input", type=Path, help="Local JSON export produced by Local X Bookmark Exporter")
    parser.add_argument("--json-out", type=Path, help="Write deterministic JSON receipt to this path")
    parser.add_argument("--markdown-out", type=Path, help="Write deterministic Markdown receipt to this path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        receipt = build_receipt(args.input)
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    json_text = deterministic_json(receipt)
    markdown_text = receipt_to_markdown(receipt)
    if args.json_out:
        write_text(args.json_out, json_text)
    if args.markdown_out:
        write_text(args.markdown_out, markdown_text)
    if not args.json_out and not args.markdown_out:
        sys.stdout.write(json_text)
    if not receipt["valid"]:
        for error in receipt["errors"]:
            print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
