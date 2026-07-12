<p align="center">
  <img src="icons/icon128.png" width="96" height="96" alt="Local X Bookmark Exporter icon">
</p>

<h1 align="center">Local X Bookmark Exporter</h1>

<p align="center">
  Export the bookmark cards visible in your signed-in X account to JSON, CSV, or Markdown.
  No API key, backend, tracking, or account credential capture.
</p>

> [!IMPORTANT]
> This project is not affiliated with, endorsed by, or sponsored by X Corp. X can change its page structure at any time, which may require updates to the scraper.

## What it does

Local X Bookmark Exporter is a small Manifest V3 Chrome extension. You open your X bookmarks page, click the extension, and leave the tab open while it scrolls through the timeline. The extension reads rendered bookmark cards, removes duplicate post IDs, and saves a file to your Downloads folder.

It supports:

- JSON, CSV, and Markdown exports
- visible post text, author, timestamp, canonical URL, language, and media URLs
- automatic scrolling with configurable delays
- duplicate removal by post ID
- a maximum-record limit for smaller exports
- partial export when you stop a run
- an in-page progress panel
- automatic interface localization based on Chrome's UI language

## Privacy model

The extension was built around a narrow permission boundary.

| Behavior | Included? |
| --- | --- |
| Official X API key | No |
| Calls to X's internal GraphQL API | No |
| Password access | No |
| Cookie access | No |
| Authorization-header capture | No |
| Remote backend | No |
| Analytics or telemetry | No |
| Persistent access to x.com | No |
| Temporary access after you click the extension | Yes |
| Local file download | Yes |

The extension requests only:

- `activeTab`: temporary access to the tab where you clicked the extension
- `scripting`: injects the local exporter code into that active tab

There are no `host_permissions`, background workers, content scripts that run on every page, remote scripts, or programmatic network requests in the runtime code.

Your exported file may contain private bookmark data. Store and share it with the same care you would use for any private account archive.

## Install from source

The extension is not currently published in the Chrome Web Store. Install it as an unpacked extension:

1. Download an extension package:
   - Open the [latest GitHub release](https://github.com/0xOzen/local-x-bookmark-exporter/releases/latest), download `local-x-bookmark-exporter-v<version>.zip`, and extract it, or
   - Click **Code > Download ZIP** on the repository page and extract it, or
   - Clone the source with:

     ```bash
     git clone https://github.com/0xOzen/local-x-bookmark-exporter.git
     ```

2. Open Chrome and visit:

   ```text
   chrome://extensions
   ```

3. Turn on **Developer mode**.
4. Click **Load unpacked**.
5. Select the extracted repository folder, the folder that contains `manifest.json`.
6. Optionally pin **Local X Bookmark Exporter** from Chrome's extensions menu.

Chrome shows a warning for extensions installed in Developer mode. That is expected for any unpacked extension.

## Export bookmarks

1. Sign in to X in Chrome.
2. Open:

   ```text
   https://x.com/i/bookmarks
   ```

3. Wait for the bookmark timeline to load.
4. Click the extension icon.
5. Choose JSON, CSV, or Markdown.
6. Click **Start export**.
7. Keep the X tab open until the progress panel reports completion.
8. Open the downloaded file from your Downloads folder.

JSON is the best format for backups, scripts, and later processing. CSV is convenient for spreadsheets. Markdown is useful for plain-text archives and note systems.

## Advanced settings

| Setting | Default | Use it when |
| --- | ---: | --- |
| Wait between scrolls | 1.8 seconds | Increase it if X loads slowly or records appear to be skipped |
| Stop after no new records | 10 passes | Increase it for very large or slow-loading timelines |
| Maximum bookmarks | 0, unlimited | Set a number for a small test export |

For large archives, try a 2.5-second delay and 15 empty passes.

## Exported data

A JSON export has this shape:

```json
{
  "meta": {
    "schemaVersion": 1,
    "sourcePage": "https://x.com/i/bookmarks",
    "method": "local DOM scrolling",
    "completeness": "best-effort; X does not expose a total count to this exporter",
    "startedAt": "2026-07-12T12:00:00.000Z",
    "exportedAt": "2026-07-12T12:04:10.000Z",
    "count": 2,
    "stopReason": "no-new-cards",
    "options": {
      "format": "json",
      "scrollDelayMs": 1800,
      "maxIdleRounds": 10,
      "maxBookmarks": 0
    }
  },
  "bookmarks": [
    {
      "id": "1234567890123456789",
      "url": "https://x.com/example/status/1234567890123456789",
      "authorHandle": "example",
      "authorName": "Example User",
      "postedAt": "2026-07-10T10:00:00.000Z",
      "text": "Example bookmarked post.",
      "language": "en",
      "mediaUrls": [],
      "capturedAt": "2026-07-12T12:00:05.000Z"
    }
  ]
}
```

`capturedAt` is the time the extension read the rendered card. X does not expose the original time when you added a bookmark to this DOM-based exporter.

## Supported interface languages

Chrome selects the extension locale from your browser UI language. The current package includes:

- English
- Turkish
- German
- Spanish
- French
- Portuguese, Brazil
- Italian
- Japanese
- Simplified Chinese

New translations are welcome. Every locale must contain the same message keys as `_locales/en/messages.json`.

## Accuracy and limitations

This exporter reads the rendered page. That privacy choice has tradeoffs:

- X does not expose a total bookmark count to the extension, so completeness is best-effort.
- Deleted, protected, withheld, or otherwise unavailable posts may not be readable.
- A slow connection can delay cards beyond the configured stop threshold.
- X uses a virtualized timeline. Only cards that load while scrolling can be collected.
- X can rename DOM attributes or change its timeline structure.
- Media URLs are saved, but media files are not downloaded.
- Premium bookmark folders are not enumerated through an internal API. If you open a specific bookmark folder route, the extension exports cards rendered on that route.

The JSON metadata records the stop reason and explicitly labels the result as best-effort.

## How it works

1. The popup verifies that the active page is an `x.com/i/bookmarks` route.
2. Chrome grants temporary `activeTab` access because the user clicked the extension.
3. The extension injects local parsing, localization, and export scripts.
4. The scraper reads `article[data-testid="tweet"]` cards that contain a bookmark-removal control.
5. It extracts stable post identifiers and visible fields.
6. A map keyed by post ID removes duplicates while the timeline scrolls.
7. The exporter serializes the records in the selected format.
8. A Blob URL triggers a local browser download.

The runtime code does not use `fetch`, XHR, WebSocket, cookie APIs, request interception, remote code, or `eval`.

## Repository layout

```text
_locales/                 Chrome localization files
icons/                    Extension icons
scripts/generate_icons.py Optional icon generator
scripts/package_extension.py Build the GitHub Release ZIP
content.js                Scroll loop, progress panel, local download
scraper.js                DOM parsing and record extraction
lib.js                    Serialization and file helpers
i18n.js                   Runtime localization helper
popup.html/css/js          Extension popup
manifest.json             Manifest V3 configuration
tests/                    Security, localization, and Chrome fixture tests
```

## Development and tests

Requirements:

- Node.js, used for JavaScript syntax checks
- Python 3.9 or newer
- Google Chrome or Chromium

Run the full test suite:

```bash
./tests/run-tests.sh
```

The suite checks:

- JavaScript syntax
- exact minimal permissions
- absence of network, cookie, token, request-interception, and dynamic-code APIs
- consistency across all locale files
- DOM parsing and deduplication
- localization fallback and placeholders
- JSON download generation
- CSV escaping and UTF-8 BOM output
- real Chrome execution through a local fixture
- exact runtime-only contents of the GitHub Release ZIP
- public-release paths and secret patterns when run inside Git

The tests use only the standard Python library for browser control. The optional icon generator uses Pillow:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install Pillow
python scripts/generate_icons.py
```

## Contributing

Bug reports, selector fixes, translations, accessibility improvements, and export-format improvements are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

Do not attach a real bookmark export to a public issue. Use a minimal, sanitized HTML example or fictional fixture data.

## Security

Read [SECURITY.md](SECURITY.md) for the threat model and private reporting path. Any proposal that adds persistent host permissions, authentication access, request interception, remote code, telemetry, or a backend changes the project's security model and requires explicit review.

## Source notes

[SOURCES.md](SOURCES.md) explains the design choices and the open-source projects reviewed during the initial implementation.

## License

MIT. See [LICENSE](LICENSE).
