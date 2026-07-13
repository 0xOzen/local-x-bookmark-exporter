# Dependency and license inventory

Release candidate: Local X Bookmark Exporter v1.2.0

## Runtime artifacts

| Artifact | Runtime dependencies | License notes |
| --- | --- | --- |
| `local-x-bookmark-exporter-v1.2.0.zip` | None beyond Chrome/Chromium extension APIs. No bundled third-party JavaScript, CSS, fonts, or binary libraries. | Project code and bundled assets are distributed under the repository MIT license. |
| `x-bookmark-companion-tools-v0.1.0.zip` | Python standard library only. No bundled third-party Python packages. | Project code, fictional examples, docs, and generated sample outputs are distributed under the repository MIT license. |

## Build-only optional tooling

`scripts/generate_icons.py` can use Pillow when regenerating icon PNG files. Pillow is optional, build-only, not required to install or run the Chrome extension, not required to run Archive Doctor or Evidence Pack, and is not bundled in either release ZIP. Pillow's upstream license expression is `MIT-CMU`; see [PyPI](https://pypi.org/project/pillow/) and the [upstream LICENSE](https://github.com/python-pillow/Pillow/blob/main/LICENSE).

No Pillow version is recorded here because the repository does not pin or vendor Pillow for this release candidate.

## SBOM

The deterministic CycloneDX SBOM for this release candidate is `sbom.cdx.json`. It records the repository component and intentionally has an empty third-party component list because no third-party runtime dependency is bundled in either intended release artifact.

## Provenance

Clean-room implementation and reference/source notes are documented in `SOURCES.md`. No `THIRD_PARTY_NOTICES.md` file is included because this release candidate does not bundle a third-party component that requires a separate notice file.
