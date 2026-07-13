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
FIXED_TIME = (2026, 1, 1, 0, 0, 0)

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
        relative = path.relative_to(ROOT).as_posix()
        info = zipfile.ZipInfo(relative, FIXED_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, path.read_bytes())

print(output)
