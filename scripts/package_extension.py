#!/usr/bin/env python3
"""Build a clean, installable ZIP for GitHub Releases."""

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
version = manifest["version"]
output_dir = ROOT / "dist"
output_dir.mkdir(parents=True, exist_ok=True)
output = output_dir / f"local-x-bookmark-exporter-v{version}.zip"

files = [
    ROOT / "manifest.json",
    ROOT / "lib.js",
    ROOT / "scraper.js",
    ROOT / "i18n.js",
    ROOT / "content.js",
    ROOT / "popup.html",
    ROOT / "popup.css",
    ROOT / "popup.js",
]
files.extend(sorted((ROOT / "icons").glob("*.png")))
files.extend(sorted((ROOT / "_locales").glob("*/messages.json")))

with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(path)
        archive.write(path, path.relative_to(ROOT).as_posix())

print(output)
