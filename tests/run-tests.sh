#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

for file in lib.js scraper.js i18n.js content.js popup.js; do
  node --check "$ROOT/$file"
done
printf '%s\n' "PASS JavaScript syntax: 5 files"

python3 "$ROOT/tests/security_audit.py"
python3 "$ROOT/tests/public_release_audit.py"
python3 "$ROOT/tests/package_audit.py"
python3 "$ROOT/tests/run_browser_test.py"

printf '%s\n' "ALL TESTS PASSED"
