# Security policy

## Supported versions

Security fixes are applied to the latest release on the default branch.

| Version | Supported |
| --- | --- |
| 1.2.x | Yes |
| 1.1.x | No |
| Older versions | No |

## Report a vulnerability

Do not open a public issue for a vulnerability that could expose account data, exported bookmarks, browser session information, or local files.

Use GitHub's private vulnerability reporting flow:

https://github.com/0xOzen/local-x-bookmark-exporter/security/advisories/new

Include:

- affected version or commit
- browser and operating system
- clear reproduction steps
- expected and observed behavior
- the smallest sanitized proof of concept

Do not include real bookmark exports, cookies, tokens, passwords, or unrelated browser data.

## Security model

The runtime is designed to:

- run only after the user clicks the extension
- accept temporary `activeTab` access
- inject bundled local scripts into the active X bookmarks tab
- read rendered bookmark cards
- create a local Blob download

The runtime must not:

- read passwords, cookies, local storage, or session tokens
- capture authorization or request headers
- call X's official or internal APIs
- send data to a remote backend
- load remote code
- add analytics or telemetry
- request persistent host permissions without a documented security review
- use dynamic code execution such as `eval`

Automated tests scan the runtime and manifest for these boundaries.

## Companion-tool security model

The optional Python companion tools are designed to:

- read local JSON exports produced by this exporter
- validate exporter schema, metadata, IDs, URLs, timestamps, media URL shape, duplicates, hostile strings, and unsupported future schemas
- write local deterministic receipts or Markdown evidence packs
- compute hashes for provenance and repeated-run verification

The companion tools must not:

- call X's official or internal APIs
- open or automate a browser session
- upload exports or generated notes to a remote service
- use AI summarization or enrichment
- mutate the input export
- include real bookmark exports in fixtures, examples, tests, screenshots, or public issues

The generated files can still contain private bookmark data when run on a real export. Treat them with the same care as the original export.

Release-candidate dependency evidence is tracked in `DEPENDENCIES.md` and `sbom.cdx.json`. The Chrome extension runtime has no bundled third-party runtime dependencies, the companion tools use the Python standard library only, and optional Pillow usage is limited to build-time icon regeneration.

## Data handling

Exports remain on the user's device unless the user shares them. The project has no server and cannot recover deleted exports.

Export files may contain:

- post text
- account names and handles
- timestamps
- canonical post URLs
- media URLs

Users should treat exports as private account archives.

Archive Doctor receipts and Evidence Pack Markdown files may include source URLs, handles, timestamps, media links, and post text from the export. Do not publish those outputs unless they were generated from fictional or fully sanitized data.

## Known limitations that are not vulnerabilities

- DOM scraping can break when X changes its markup.
- A best-effort export may miss cards that never load.
- Deleted or inaccessible posts cannot be reconstructed.
- Media URLs are references to already rendered content; the extension does not download the media files.
- Developer mode installation produces Chrome warnings that apply to all unpacked extensions.
