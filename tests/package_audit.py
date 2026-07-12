#!/usr/bin/env python3
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
version = manifest["version"]

subprocess.run(["python3", str(ROOT / "scripts" / "package_extension.py")], cwd=ROOT, check=True, capture_output=True)
archive_path = ROOT / "dist" / f"local-x-bookmark-exporter-v{version}.zip"
assert archive_path.is_file()

with zipfile.ZipFile(archive_path) as archive:
    names = set(archive.namelist())
    packaged_manifest = json.loads(archive.read("manifest.json"))

required = {
    "manifest.json",
    "lib.js",
    "scraper.js",
    "i18n.js",
    "content.js",
    "popup.html",
    "popup.css",
    "popup.js",
    "icons/icon16.png",
    "icons/icon32.png",
    "icons/icon48.png",
    "icons/icon128.png",
}
required.update(f"_locales/{locale}/messages.json" for locale in ("en", "tr", "de", "es", "fr", "pt_BR", "it", "ja", "zh_CN"))

assert names == required, (sorted(names), sorted(required))
assert packaged_manifest["version"] == version
assert not any(name.startswith(("tests/", "scripts/", ".github/")) for name in names)
assert not any(name.endswith(".md") for name in names)

print(f"PASS release package audit: {archive_path.name}, {len(names)} runtime files")
