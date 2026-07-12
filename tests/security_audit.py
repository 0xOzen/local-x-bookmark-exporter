#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

assert manifest["manifest_version"] == 3
assert manifest["default_locale"] == "en"
assert manifest["name"] == "__MSG_appName__"
assert manifest["description"] == "__MSG_appDescription__"
assert set(manifest.get("permissions", [])) == {"activeTab", "scripting"}
assert "host_permissions" not in manifest
assert "content_scripts" not in manifest
assert "background" not in manifest

expected_locales = {"en", "tr", "de", "es", "fr", "pt_BR", "it", "ja", "zh_CN"}
locale_root = ROOT / "_locales"
actual_locales = {path.name for path in locale_root.iterdir() if path.is_dir()}
assert actual_locales == expected_locales, (actual_locales, expected_locales)

locale_payloads = {
    locale: json.loads((locale_root / locale / "messages.json").read_text(encoding="utf-8"))
    for locale in expected_locales
}
english_keys = set(locale_payloads["en"])
assert len(english_keys) == 39
for locale, payload in locale_payloads.items():
    assert set(payload) == english_keys, f"{locale}: localization key mismatch"
    for key, entry in payload.items():
        assert isinstance(entry.get("message"), str) and entry["message"].strip(), f"{locale}/{key}: empty message"
    assert set(payload["scanProgress"].get("placeholders", {})) == {"cycle", "idle"}
    assert set(payload["downloadComplete"].get("placeholders", {})) == {"count"}

runtime_files = ["lib.js", "scraper.js", "i18n.js", "content.js", "popup.js"]
forbidden = {
    "fetch(": "programmatic network request",
    "XMLHttpRequest": "programmatic network request",
    "WebSocket": "programmatic network request",
    "chrome.cookies": "cookie access",
    "chrome.webRequest": "request-header access",
    "declarativeNetRequest": "network interception",
    "Authorization": "authorization-header handling",
    "eval(": "dynamic code execution",
}

for filename in runtime_files:
    source = (ROOT / filename).read_text(encoding="utf-8")
    for token, description in forbidden.items():
        assert token not in source, f"{filename}: forbidden {description}: {token}"

popup = (ROOT / "popup.html").read_text(encoding="utf-8")
assert "<script src=\"http" not in popup
assert "<script src='http" not in popup
for key in re.findall(r'data-i18n="([^"]+)"', popup):
    assert key in english_keys, f"popup.html: unknown localization key {key}"

popup_script = (ROOT / "popup.js").read_text(encoding="utf-8")
assert 'files: ["lib.js", "scraper.js", "i18n.js", "content.js"]' in popup_script

print(
    "PASS security and localization audit: "
    "minimal temporary permissions, no network/session APIs, 9 complete locales"
)
