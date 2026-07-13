#!/usr/bin/env python3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = [ROOT / "README.md", ROOT / "KURULUM.md"]
OLD_BROKEN_COMMAND = (
    "python3 tools/x_bookmark_evidence_pack.py "
    "examples/x-bookmark-export-fictional.json examples/evidence-pack"
)
FRESH_OUTPUT_ASSIGNMENT = 'OUTPUT_DIR="$(mktemp -d)/x-bookmark-evidence-pack-demo"'
DOCUMENTED_COMMAND = (
    "python3 tools/x_bookmark_evidence_pack.py "
    'examples/x-bookmark-export-fictional.json "$OUTPUT_DIR"'
)


def assert_contains(haystack, needle, label):
    assert needle in haystack, f"{label}: missing {needle!r}"


for doc in DOCS:
    text = doc.read_text(encoding="utf-8")
    assert OLD_BROKEN_COMMAND not in text, f"{doc.name}: old Evidence Pack command writes into shipped examples/evidence-pack"
    assert_contains(text, FRESH_OUTPUT_ASSIGNMENT, doc.name)
    assert_contains(text, DOCUMENTED_COMMAND, doc.name)

readme = (ROOT / "README.md").read_text(encoding="utf-8")
assert_contains(readme, "The output path must not already exist", "README.md")
assert_contains(readme, "choose a new output directory name for another run", "README.md")

kurulum = (ROOT / "KURULUM.md").read_text(encoding="utf-8")
assert_contains(kurulum, "Çıktı yolu önceden var olmamalı", "KURULUM.md")
assert_contains(kurulum, "başka bir çalıştırma için yeni bir klasör adı seç", "KURULUM.md")

with tempfile.TemporaryDirectory() as directory:
    output_dir = Path(directory) / "x-bookmark-evidence-pack-demo"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "x_bookmark_evidence_pack.py"),
            str(ROOT / "examples" / "x-bookmark-export-fictional.json"),
            str(output_dir),
            "--tag",
            "fictional-fixture",
            "--tag",
            "local-export",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert (output_dir / "index.md").is_file()
    assert (output_dir / "manifest.json").is_file()

assert not (ROOT / "x-bookmark-evidence-pack-demo").exists(), "docs smoke left repo output"
print("PASS docs examples audit: Evidence Pack docs use a fresh temporary output path")
