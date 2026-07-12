# Contributing

Contributions are welcome, especially selector fixes, translations, accessibility improvements, tests, and export-format corrections.

## Before opening an issue

- Search existing issues.
- Confirm the problem still occurs on the latest default branch.
- Record your Chrome version and operating system.
- Remove account names, post text, URLs, and other private data from screenshots or logs.
- Never attach a real bookmark export to a public issue.

## Development setup

1. Fork and clone the repository.
2. Create a focused branch:

   ```bash
   git switch -c fix/short-description
   ```

3. Make the smallest change that solves the problem.
4. Run:

   ```bash
   ./tests/run-tests.sh
   ```

5. Load the repository through `chrome://extensions` and test it on your own account.
6. Open a pull request with the problem, approach, and verification results.

The test suite requires Node.js, Python 3.9 or newer, and Chrome or Chromium. Runtime code has no package-manager dependencies.

## Translation changes

Chrome locale files live under `_locales/<locale>/messages.json`.

When adding or editing a translation:

- preserve every key from `_locales/en/messages.json`
- preserve the placeholders for `scanProgress` and `downloadComplete`
- use the language's normal punctuation and terminology
- test the popup and in-page progress panel
- avoid machine-translated text that has not been reviewed by a fluent speaker

The localization audit rejects missing or extra keys.

## Security boundary

Changes that add any of the following need a clear threat-model discussion:

- `host_permissions`
- cookie or storage access
- request interception
- official or internal X API calls
- remote scripts
- a backend service
- analytics or telemetry
- dynamic code execution

A convenience feature is not enough reason to broaden account access.

## DOM selector changes

Prefer attributes with a clear semantic role, such as `data-testid`, over deep `nth-child` selectors. Add a sanitized fixture that reproduces the markup change. Do not paste private page HTML into the repository.

## Pull-request scope

Keep feature work, selector fixes, formatting, and refactors separate when possible. Pull requests should include:

- what changed
- why it changed
- tests run
- privacy or permission impact
- known limitations

## Code style

- plain JavaScript, HTML, CSS, and Python
- no build step for extension runtime files
- no remote dependencies in the extension
- clear names and small functions
- straight quotes and simple prose in public documentation
