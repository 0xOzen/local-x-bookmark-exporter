#!/usr/bin/env python3
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

result = subprocess.run(
    ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
    cwd=ROOT,
    check=True,
    capture_output=True,
)
paths = [Path(value.decode("utf-8")) for value in result.stdout.split(b"\0") if value]
assert paths, "No public release candidates found"

blocked_paths = [
    re.compile(r"(^|/)\.tests-output(/|$)"),
    re.compile(r"(^|/)\.private(/|$)"),
    re.compile(r"(^|/)RELATED-PROJECTS\.md$"),
    re.compile(r"(^|/)\.env(?:\.|$)"),
    re.compile(r"\.(?:pem|key)$", re.IGNORECASE),
]

for path in paths:
    normalized = path.as_posix()
    for pattern in blocked_paths:
        assert not pattern.search(normalized), f"Blocked public path: {normalized}"

blocked_text = [
    (re.compile(r"/Users/[^/\s]+/"), "absolute macOS user path"),
    (re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+"), "absolute Windows user path"),
    (re.compile(r"\bAli OS\b"), "private operating-system reference"),
    (re.compile(r"\bPersonal Brand\b"), "private project reference"),
    (re.compile(r"\bObsidian\b"), "private knowledge-system reference"),
    (re.compile(r"\bdevs-world\b"), "private project reference"),
    (re.compile(r"\bJanus analysis\b", re.IGNORECASE), "private workflow reference"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key material"),
    (re.compile(r"gh" + r"[pousr]_[A-Za-z0-9]{20,}"), "GitHub token"),
    (re.compile(r"github" + r"_pat_[A-Za-z0-9_]{20,}"), "GitHub fine-grained token"),
    (re.compile(r"sk" + r"-[A-Za-z0-9]{20,}"), "API key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r"xox" + r"[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
]

assert blocked_text[0][0].search("/Users/example/private.txt")
assert blocked_text[1][0].search(r"C:\Users\example\private.txt")

for relative in paths:
    absolute = ROOT / relative
    if not absolute.is_file() or absolute.resolve() == SELF:
        continue
    data = absolute.read_bytes()
    if b"\0" in data:
        continue
    text = data.decode("utf-8", errors="replace")
    for pattern, label in blocked_text:
        assert not pattern.search(text), f"{relative}: blocked {label}"

print(f"PASS public release audit: {len(paths)} candidate files, no private paths or high-confidence secrets")
