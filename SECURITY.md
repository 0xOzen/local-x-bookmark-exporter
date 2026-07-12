# Security policy

## Supported versions

Security fixes are applied to the latest release on the default branch.

| Version | Supported |
| --- | --- |
| 1.1.x | Yes |
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

## Data handling

Exports remain on the user's device unless the user shares them. The project has no server and cannot recover deleted exports.

Export files may contain:

- post text
- account names and handles
- timestamps
- canonical post URLs
- media URLs

Users should treat exports as private account archives.

## Known limitations that are not vulnerabilities

- DOM scraping can break when X changes its markup.
- A best-effort export may miss cards that never load.
- Deleted or inaccessible posts cannot be reconstructed.
- Media URLs are references to already rendered content; the extension does not download the media files.
- Developer mode installation produces Chrome warnings that apply to all unpacked extensions.
