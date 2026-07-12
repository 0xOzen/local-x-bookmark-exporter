# Changelog

All notable changes are documented here.

The project follows [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-07-12

Initial public release.

### Added

- local DOM-based X bookmark export
- JSON, CSV, and Markdown formats
- automatic scrolling with configurable delays and stop thresholds
- post-ID deduplication
- page-local progress and stop controls
- best-effort completeness metadata and stop reasons
- Chrome localization for English, Turkish, German, Spanish, French, Brazilian Portuguese, Italian, Japanese, and Simplified Chinese
- minimal-permission security audit
- real Chrome fixture covering parsing, localization, download generation, JSON, and CSV
- public-release audit for private paths and high-confidence secret patterns
- clean runtime-only ZIP packaging for GitHub Releases
- GitHub Actions CI

### Security

- no host permissions
- no cookies, request headers, session tokens, or internal X API calls
- no backend, telemetry, remote code, or dynamic code execution
