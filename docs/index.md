# Formalization Readiness Engine

The Formalization Readiness Engine (FRE) is an artifact-first research system for measuring how close informal mathematical statements are to machine-checkable formalization in Lean/mathlib.

## What you can do with this repository

- Run the end-to-end demo on two reference examples (`make demo`).
- Inspect hand-authored artifact stacks under `examples/`.
- Score predicted readiness reports against ReadinessBench gold fixtures.
- Export public JSONL artifacts for benchmarks and the Formalization Gap Atlas.
- Review readiness reports through the thin API and static review UI.
- Ingest author-permitted LaTeX sources and promote units into ReadinessBench bronze tier.

## Release snapshot (v0.2.0)

| Metric | Value |
|--------|-------|
| ReadinessBench items | 43 (11 gold, 1 silver, 31 bronze) |
| Corpus units | 30 from 5 catalog sources |
| Unit tests | 165 |
| Lean pin | Lean 4.8.0 + mathlib v4.8.0 |

## Quick start

**Linux and macOS:**

```bash
make setup
make demo
```

**Windows (PowerShell):**

```powershell
.\scripts\dev.ps1 setup
.\scripts\dev.ps1 demo
```

## Documentation map

- [Architecture](ARCHITECTURE.md) — pipeline, modules, and workflows
- [End-to-end demo](DEMO.md) — offline and live demo walkthrough
- [Public release guide](PUBLIC_RELEASE.md) — benchmark and Atlas exports
- [Technical report](TECHNICAL_REPORT.md) — Wave 6 release summary
- [Docker Compose](DOCKER.md) — API, worker, Redis/RQ jobs
- [Corpus governance](CORPUS_GOVERNANCE.md) — catalog, release modes, bronze promotion
- [OpenAI usage](OPENAI_USAGE.md) — model-call conventions
- [Engineering handoff](ENGINEERING_HANDOFF.md) — takeover guide for contributors
- [Implementation plan](IMPLEMENTATION_PLAN.md) — long-term technical foundation
- [Next sprints](NEXT_SPRINTS.md) — completed sprints and optional follow-on work

External review:

- [Reviewer guide](review/REVIEWER_GUIDE.md)
- [Review form](review/READINESS_REPORT_REVIEW_FORM.md)
- [Usefulness rubric](review/USEFULNESS_RUBRIC.md)

## Build this site locally

```bash
make docs
```

MkDocs configuration lives in `apps/docs-site/mkdocs.yml`. Sources are the `docs/` directory at the repository root.

## Citation

```text
Formalization Readiness Engine (v0.2.0).
https://github.com/fraware/formalization-readiness-engine
Release manifest: releases/v0.2.0/manifest.json
```
