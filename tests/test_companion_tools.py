#!/usr/bin/env python3
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
VALID = FIXTURES / "x-bookmark-export-valid-fictional.json"

sys.path.insert(0, str(ROOT))

from x_bookmark_tools.archive_doctor import (  # noqa: E402
    build_receipt,
    receipt_to_markdown,
    validate_export_file,
)
from x_bookmark_tools.evidence_pack import build_evidence_pack, ensure_output_path_is_new  # noqa: E402


def assert_contains(haystack, needle):
    assert needle in haystack, f"missing {needle!r} in {haystack!r}"


def write_export_with(directory: Path, **meta_updates) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    payload = json.loads(VALID.read_text(encoding="utf-8"))
    payload["meta"].update(meta_updates)
    path = directory / "export.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def expect_value_error_contains(needle, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except ValueError as error:
        assert_contains(str(error), needle)
    else:
        raise AssertionError("expected ValueError")


def test_archive_doctor_accepts_valid_export_and_is_deterministic():
    first = build_receipt(VALID)
    second = build_receipt(VALID)
    expected_hash = hashlib.sha256(VALID.read_bytes()).hexdigest()

    assert first == second
    assert first["tool"] == "x-bookmark-archive-doctor"
    assert first["valid"] is True
    assert first["input_sha256"] == expected_hash
    assert first["bookmark_count"] == 2
    assert first["claimed_count"] == 2
    assert first["errors"] == []
    assert_contains(first["completeness"], "best-effort")
    assert_contains(receipt_to_markdown(first), "Never claims completeness")


def test_archive_doctor_rejects_invalid_exports_safely():
    cases = {
        "x-bookmark-export-invalid-duplicate.json": "duplicate bookmark id",
        "x-bookmark-export-invalid-count.json": "meta.count does not match",
        "x-bookmark-export-invalid-future-schema.json": "unsupported schemaVersion",
        "x-bookmark-export-invalid-hostile.json": "hostile string",
        "x-bookmark-export-invalid-path-traversal.json": "authorHandle must be an X handle",
    }
    for filename, expected in cases.items():
        receipt = build_receipt(FIXTURES / filename)
        assert receipt["valid"] is False, filename
        joined_errors = "\n".join(receipt["errors"])
        assert_contains(joined_errors, expected)


def test_archive_doctor_validates_source_page_with_strict_url_policy():
    valid_source_pages = [
        "https://x.com/i/history/bookmarks/",
        "https://x.com/i/history/bookmarks",
        "https://www.x.com/i/history/bookmarks/?cursor=abc123",
        "https://x.com:443/i/history/bookmarks/folder/123?sort=latest",
        "https://x.com/i/bookmarks",
        "https://x.com:443/i/bookmarks",
        "https://www.x.com/i/bookmarks?cursor=abc123",
        "https://x.com/i/bookmarks/folder/123?sort=latest",
    ]
    invalid_source_pages = [
        "https://x.com/i/history/bookmarksevil",
        "https://x.com/i/history",
        "http://x.com/i/history/bookmarks/",
        "https://x.com.evil.example/i/history/bookmarks/",
        "https://user:pass@x.com/i/history/bookmarks/",
        "https://x.com:444/i/history/bookmarks/",
        "https://x.com/i/history/bookmarks/#fragment",
        "http://x.com/i/bookmarks",
        "https://evil.example/i/bookmarks",
        "https://x.com.evil.example/i/bookmarks",
        "https://user:pass@x.com/i/bookmarks",
        "https://x.com:444/i/bookmarks",
        "https://x.com/i/bookmarksevil",
        "https://x.com/i/bookmarks#fragment",
    ]
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        for index, source_page in enumerate(valid_source_pages):
            receipt = build_receipt(write_export_with(tmp / f"valid-{index}", sourcePage=source_page))
            assert receipt["valid"] is True, (source_page, receipt["errors"])
            pack = build_evidence_pack(tmp / f"valid-{index}" / "export.json", tmp / f"pack-{index}")
            assert (pack.output_dir / "index.md").is_file()
        for index, source_page in enumerate(invalid_source_pages):
            receipt = build_receipt(write_export_with(tmp / f"invalid-{index}", sourcePage=source_page))
            assert receipt["valid"] is False, source_page
            assert_contains("\n".join(receipt["errors"]), "meta.sourcePage must be an HTTPS X bookmarks route")


def test_evidence_pack_writes_deterministic_obsidian_compatible_markdown():
    with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
        first = build_evidence_pack(VALID, Path(first_dir) / "pack", tags=["fictional-fixture", "local-export"])
        second = build_evidence_pack(VALID, Path(second_dir) / "pack", tags=["fictional-fixture", "local-export"])

        first_files = sorted(path.relative_to(first.output_dir).as_posix() for path in first.output_dir.rglob("*") if path.is_file())
        second_files = sorted(path.relative_to(second.output_dir).as_posix() for path in second.output_dir.rglob("*") if path.is_file())
        assert first_files == second_files
        assert first.manifest == second.manifest
        assert "index.md" in first_files
        assert "manifest.json" in first_files
        assert len([name for name in first_files if name.startswith("bookmarks/") and name.endswith(".md")]) == 2

        for relative in first_files:
            assert ".." not in relative
            assert first.output_dir.joinpath(relative).read_bytes() == second.output_dir.joinpath(relative).read_bytes()

        index = (first.output_dir / "index.md").read_text(encoding="utf-8")
        assert_contains(index, "# X Bookmark Evidence Pack")
        assert_contains(index, "Best-effort export")
        assert_contains(index, "fictional-fixture")
        note = next((first.output_dir / "bookmarks").glob("*.md"))
        note_text = note.read_text(encoding="utf-8")
        assert_contains(note_text, "source_url:")
        assert_contains(note_text, "export_sha256:")
        assert_contains(note_text, "## Original text")


def test_evidence_pack_refuses_existing_output_paths_without_mutation():
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)

        non_empty = tmp / "non-empty-pack"
        non_empty.mkdir()
        non_empty_sentinel = non_empty / "keep.txt"
        non_empty_sentinel.write_text("keep", encoding="utf-8")
        expect_value_error_contains("output path already exists", build_evidence_pack, VALID, non_empty)
        assert non_empty_sentinel.read_text(encoding="utf-8") == "keep"
        assert not (non_empty / "index.md").exists()

        empty = tmp / "empty-pack"
        empty.mkdir()
        expect_value_error_contains("output path already exists", build_evidence_pack, VALID, empty)
        assert empty.is_dir()
        assert list(empty.iterdir()) == []

        existing_file = tmp / "pack-file"
        existing_file.write_text("file sentinel", encoding="utf-8")
        expect_value_error_contains("output path already exists", build_evidence_pack, VALID, existing_file)
        assert existing_file.read_text(encoding="utf-8") == "file sentinel"

        root_like_existing = tmp / "root-like"
        root_like_existing.mkdir()
        root_sentinel = root_like_existing / "repo-file.txt"
        root_sentinel.write_text("repo sentinel", encoding="utf-8")
        expect_value_error_contains("output path already exists", build_evidence_pack, VALID, root_like_existing)
        assert root_sentinel.read_text(encoding="utf-8") == "repo sentinel"


def test_evidence_pack_refuses_symlink_output_without_touching_target():
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        target = tmp / "target"
        target.mkdir()
        target_sentinel = target / "keep.txt"
        target_sentinel.write_text("keep target", encoding="utf-8")
        output_link = tmp / "linked-pack"
        output_link.symlink_to(target, target_is_directory=True)

        expect_value_error_contains("output path already exists", build_evidence_pack, VALID, output_link)

        assert output_link.is_symlink()
        assert target_sentinel.read_text(encoding="utf-8") == "keep target"
        assert not (target / "index.md").exists()


def test_evidence_pack_no_existing_path_rule_covers_repo_root_and_home():
    for unsafe_existing_path in (ROOT, Path.home()):
        expect_value_error_contains("output path already exists", ensure_output_path_is_new, unsafe_existing_path)


def test_evidence_pack_validates_and_sorts_tag_grammar():
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        result = build_evidence_pack(
            VALID,
            tmp / "pack",
            tags=["local-export", "Fictional_1", "alpha.beta", "local-export"],
        )
        assert result.manifest["tags"] == ["Fictional_1", "alpha.beta", "local-export"]

        invalid_tags = ["", "_leading", "bad|tag", "bad\ntag", "a" * 65]
        for index, tag in enumerate(invalid_tags):
            output_dir = tmp / f"invalid-tag-{index}"
            expect_value_error_contains("tag must match", build_evidence_pack, VALID, output_dir, tags=[tag])
            assert not output_dir.exists()


def test_evidence_pack_cli_rejects_unsafe_tags_without_writing():
    with tempfile.TemporaryDirectory() as directory:
        output_dir = Path(directory) / "pack"
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "x_bookmark_evidence_pack.py"),
                str(VALID),
                str(output_dir),
                "--tag",
                "safe-tag",
                "--tag",
                "bad|tag",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 1
        assert_contains(completed.stderr, "tag must match")
        assert not output_dir.exists()


def test_evidence_pack_requires_valid_export_before_writing():
    with tempfile.TemporaryDirectory() as directory:
        output_dir = Path(directory) / "pack"
        try:
            build_evidence_pack(FIXTURES / "x-bookmark-export-invalid-count.json", output_dir)
        except ValueError as error:
            assert_contains(str(error), "valid local JSON export")
        else:
            raise AssertionError("invalid export unexpectedly accepted")
        assert not output_dir.exists()


def test_cli_help_and_valid_runs_are_deterministic():
    commands = [
        [sys.executable, str(ROOT / "tools" / "x_bookmark_archive_doctor.py"), "--help"],
        [sys.executable, str(ROOT / "tools" / "x_bookmark_evidence_pack.py"), "--help"],
    ]
    for command in commands:
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
        assert_contains(completed.stdout, "usage:")

    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        receipt_json = tmp / "receipt.json"
        receipt_md = tmp / "receipt.md"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "x_bookmark_archive_doctor.py"),
                str(VALID),
                "--json-out",
                str(receipt_json),
                "--markdown-out",
                str(receipt_md),
            ],
            cwd=ROOT,
            check=True,
        )
        first_json = receipt_json.read_bytes()
        first_md = receipt_md.read_bytes()
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "x_bookmark_archive_doctor.py"),
                str(VALID),
                "--json-out",
                str(receipt_json),
                "--markdown-out",
                str(receipt_md),
            ],
            cwd=ROOT,
            check=True,
        )
        assert first_json == receipt_json.read_bytes()
        assert first_md == receipt_md.read_bytes()

        first_pack = tmp / "pack-a"
        second_pack = tmp / "pack-b"
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "x_bookmark_evidence_pack.py"), str(VALID), str(first_pack), "--tag", "fictional"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "x_bookmark_evidence_pack.py"), str(VALID), str(second_pack), "--tag", "fictional"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        for first_path in sorted(path for path in first_pack.rglob("*") if path.is_file()):
            relative = first_path.relative_to(first_pack)
            assert first_path.read_bytes() == second_pack.joinpath(relative).read_bytes()


def main():
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS companion tools: {len(tests)} archive doctor and evidence pack checks")


if __name__ == "__main__":
    main()
