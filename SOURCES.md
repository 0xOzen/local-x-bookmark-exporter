# Design sources and decisions

This project was implemented independently for a narrow local-only privacy model. The following open-source work was reviewed for patterns and tradeoffs.

## sytelus/xarchive

Source: https://github.com/sytelus/xarchive

Useful ideas:

- local-first export
- visible progress
- pause and partial-download behavior
- explicit privacy documentation

Not adopted:

- internal GraphQL requests
- passive authorization-header capture

Those capabilities can improve completeness, but they require a broader account-access boundary than this project accepts.

## celikomer/x-bookmark-exporter-chrome-extension

Source: https://github.com/celikomer/x-bookmark-exporter-chrome-extension

Useful ideas:

- rendered-DOM extraction
- stable `data-testid` selectors
- scrolling and post-ID deduplication
- JSON and CSV output

This repository uses its own implementation with temporary `activeTab` access, no persistent host permission, explicit best-effort metadata, Markdown output, localization, a page-local progress panel, and automated security checks.

## Chrome extension automation change

Chromium announced the removal of the `--load-extension` command-line flag from Chrome-branded builds starting with Chrome 137. Developer mode still supports manual unpacked-extension installation.

Source: https://groups.google.com/a/chromium.org/g/chromium-extensions/c/1-g8EFx2BBY

Because of that change, automated tests validate the manifest policy and runtime behavior separately. The final unpacked installation is performed through Chrome's visible Developer mode flow.

## Companion-tool format references

The Python companion tools were implemented clean-room with the Python standard library. They use this repository's documented JSON export shape as the source of truth and do not copy code, tests, examples, branding, or generated assets from external projects.

The release-candidate dependency/license inventory is in `DEPENDENCIES.md`, and the deterministic CycloneDX SBOM is in `sbom.cdx.json`. They record no bundled third-party runtime dependencies for the extension and Python standard-library-only runtime behavior for the companion tools.

Pattern references reviewed:

- Obsidian Importer, source: https://github.com/obsidianmd/obsidian-importer

Useful idea:

- portable file-based Markdown import/output can remain useful without a cloud service or proprietary database

Not adopted:

- Obsidian-specific APIs, plugins, packaging, importer code, or endorsement language

The Evidence Pack output is described only as Obsidian-compatible plain Markdown. That is a file-format compatibility statement, not affiliation, sponsorship, or endorsement.

## Project decisions

Adopted:

- temporary `activeTab` access
- local file generation
- rendered-DOM parsing
- conservative scrolling
- post-ID deduplication
- visible progress and explicit stop reasons

Rejected:

- password, cookie, token, or authorization-header access
- internal X API calls
- remote services
- analytics and telemetry
- persistent host permissions
- remote code execution
- browser automation, network calls, AI summarization, or input mutation in local companion tools

Parked until there is evidence of need:

- resumable IndexedDB checkpoints
- internal-API folder enumeration
- automatic media downloads
- Chrome Web Store distribution
