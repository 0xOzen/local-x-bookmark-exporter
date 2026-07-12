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

Parked until there is evidence of need:

- resumable IndexedDB checkpoints
- internal-API folder enumeration
- automatic media downloads
- Chrome Web Store distribution
