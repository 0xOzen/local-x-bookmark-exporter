#!/usr/bin/env python3
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subprocess.run(["python3", str(ROOT / "scripts" / "package_companion_tools.py")], cwd=ROOT, check=True, capture_output=True)
archive_path = ROOT / "dist" / "x-bookmark-companion-tools-v0.1.0.zip"
assert archive_path.is_file()

expected = {
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
}
expected.update({
    "examples/evidence-pack/bookmarks/2026-07-10-example-alpha-1234567890123456789-fictional-note-about-local-first-archive-practice.md",
    "examples/evidence-pack/bookmarks/2026-07-11-example-beta-9876543210987654321-fictional-reminder-exported-bookmarks-are-private-archives.md",
})

with zipfile.ZipFile(archive_path) as archive:
    names = set(archive.namelist())
    assert names == expected, (sorted(names), sorted(expected))
    for name in names:
        assert not name.startswith(("tests/", ".github/", ".git/", "dist/")), name
        assert "evidence/agent-runs" not in name, name
    manifest = json.loads(archive.read("examples/evidence-pack/manifest.json"))
    assert manifest["tool"] == "x-bookmark-evidence-pack"
    assert manifest["source"]["bookmark_count"] == 2
    sbom = json.loads(archive.read("sbom.cdx.json"))
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["metadata"]["component"]["version"] == "1.2.0"
    assert sbom["components"] == []

print(f"PASS companion package audit: {archive_path.name}, {len(names)} intended source/tool files")
