# Changelog

All notable changes are documented here.

The project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.2.0] - 2026-07-13

### Added

- X Bookmark Archive Doctor, a standard-library local Python validator for exporter JSON files with deterministic JSON and Markdown receipts.
- X Bookmark Evidence Pack, a standard-library local Python generator for deterministic Markdown evidence packs from validated JSON exports.
- Fictional JSON fixtures, adversarial validation cases, deterministic sample outputs, CLI help checks, and repeated-run determinism tests.
- Separate companion-tool source ZIP packaging and audit; the Chrome extension ZIP remains runtime-only.
- Deterministic CycloneDX SBOM and dependency/license inventory for the release candidate.

### Changed

- Chrome extension manifest and runtime package artifact target v1.2.0.
- Companion-tool package artifact is promoted from `x-bookmark-companion-tools-v0.1.0-local.zip` to `x-bookmark-companion-tools-v0.1.0.zip`.
- Companion-tool package now includes public support/provenance docs, dependency inventory, and SBOM alongside source, tool wrappers, and fictional examples.

### Security

- Companion tools are local-file only: no X calls, browser session, AI service, network upload, input mutation, cookies, tokens, or real bookmark fixtures.
- Public-release audit still checks private paths and high-confidence secret patterns, while allowing public docs to mention generic Obsidian-compatible Markdown.
- Dependency inventory records that the extension runtime has zero bundled third-party runtime dependencies, companion tools use Python standard library only, optional Pillow is build-only for icon regeneration, and clean-room/reference provenance remains in `SOURCES.md`.

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
