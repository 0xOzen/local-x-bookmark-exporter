#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SBOM = ROOT / "sbom.cdx.json"
raw = SBOM.read_bytes()
parsed = json.loads(raw)

assert raw == SBOM.read_text(encoding="utf-8").encode("utf-8")
assert raw.endswith(b"\n")
assert json.dumps(parsed, ensure_ascii=False, indent=2) + "\n" == raw.decode("utf-8")
assert parsed["bomFormat"] == "CycloneDX"
assert parsed["specVersion"] == "1.5"
assert parsed["version"] == 1
assert parsed["metadata"]["component"]["name"] == "local-x-bookmark-exporter"
assert parsed["metadata"]["component"]["version"] == "1.2.0"
assert parsed["components"] == []
assert parsed["dependencies"] == [
    {
        "ref": "pkg:github/0xOzen/local-x-bookmark-exporter@v1.2.0",
        "dependsOn": [],
    }
]
text = raw.decode("utf-8")
assert "0.1.0-local" not in text
assert "Pillow" in text
assert "MIT-CMU" in text
assert "https://pypi.org/project/pillow/" in text
assert "https://github.com/python-pillow/Pillow/blob/main/LICENSE" in text
assert "/Users/" not in text

print(f"PASS SBOM audit: {SBOM.name}, sha256 {hashlib.sha256(raw).hexdigest()}")
