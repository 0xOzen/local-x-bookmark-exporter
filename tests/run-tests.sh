#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

for file in lib.js scraper.js i18n.js content.js popup.js; do
  node --check "$ROOT/$file"
done
printf '%s\n' "PASS JavaScript syntax: 5 files"
node "$ROOT/tests/test_popup_routes.js"

python3 "$ROOT/tests/security_audit.py"
python3 "$ROOT/tests/public_release_audit.py"
python3 "$ROOT/tests/docs_examples_audit.py"
python3 "$ROOT/tests/sbom_audit.py"
python3 "$ROOT/tests/test_companion_tools.py"
python3 "$ROOT/tests/package_audit.py"
python3 "$ROOT/tests/companion_package_audit.py"
python3 "$ROOT/tests/run_browser_test.py"

printf '%s\n' "ALL TESTS PASSED"
