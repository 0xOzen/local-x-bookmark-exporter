#!/usr/bin/env python3
"""Build a deterministic local source/tool ZIP for the Python companions."""

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPANION_VERSION = "0.1.0"
OUTPUT = ROOT / "dist" / f"x-bookmark-companion-tools-v{COMPANION_VERSION}.zip"
FIXED_TIME = (2026, 1, 1, 0, 0, 0)
FILES = [
    "README.md",
    "KURULUM.md",
    "LICENSE",
    "SECURITY.md",
    "SOURCES.md",
    "CHANGELOG.md",
    "DEPENDENCIES.md",
    "sbom.cdx.json",
    "x_bookmark_tools/__init__.py",
    "x_bookmark_tools/archive_doctor.py",
    "x_bookmark_tools/evidence_pack.py",
    "tools/x_bookmark_archive_doctor.py",
    "tools/x_bookmark_evidence_pack.py",
    "examples/x-bookmark-export-fictional.json",
    "examples/archive-doctor-receipt.json",
    "examples/archive-doctor-receipt.md",
    "examples/evidence-pack/index.md",
    "examples/evidence-pack/manifest.json",
    "examples/evidence-pack/bookmarks/2026-07-10-example-alpha-1234567890123456789-fictional-note-about-local-first-archive-practice.md",
    "examples/evidence-pack/bookmarks/2026-07-11-example-beta-9876543210987654321-fictional-reminder-exported-bookmarks-are-private-archives.md",
]


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in FILES:
            path = ROOT / relative
            if not path.is_file():
                raise FileNotFoundError(path)
            info = zipfile.ZipInfo(relative, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    print(OUTPUT)


if __name__ == "__main__":
    main()
