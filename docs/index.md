# Formalization Readiness Engine

The Formalization Readiness Engine (FRE) is an artifact-first research system for measuring how close informal mathematical statements are to machine-checkable formalization in Lean/mathlib.

## What you can do with this repository

- Inspect hand-authored reference examples under `examples/`.
- Run ReadinessBench scoring against reviewed gold readiness reports.
- Export public JSONL artifacts for benchmarks and the Formalization Gap Atlas.
- Review readiness reports through the thin API and static review UI.

## Quick links

- [Architecture](ARCHITECTURE.md)
- [Public release guide](PUBLIC_RELEASE.md)
- [Technical report (Wave 6)](TECHNICAL_REPORT.md)
- [Engineering handoff](ENGINEERING_HANDOFF.md)

## Local documentation build

```bash
make docs
```

The MkDocs site uses sources from this `docs/` directory and configuration in `apps/docs-site/mkdocs.yml`.
