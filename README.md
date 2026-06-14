# Formalization Readiness Engine

The Formalization Readiness Engine (FRE) is an artifact-first research system for measuring how close informal mathematical statements are to machine-checkable formalization in Lean/mathlib.

Given theorem/proof units from LaTeX or author-permitted notes, the pipeline recovers source-grounded structure, identifies ambiguity and missing prerequisites, proposes mathlib alignment candidates, and emits formalization-ready LeanTask packages. Model outputs remain candidate artifacts until they pass schema validation, semantic validation, and human review.

This repository is an engineering foundation and public benchmark release, not a claim of end-to-end automated theorem proving.

## Release status (June 2026)

Waves 0–6 and Docker/RQ infrastructure are merged on `main`.

| Metric | Value |
|--------|-------|
| Unit tests | 165 (CI green) |
| ReadinessBench items | 43 (11 gold, 1 silver, 31 bronze) |
| Corpus units ingested | 30 from 5 catalog sources |
| Reference examples | `finite_tree`, `category_theory_pullback` |
| Lean pin | Lean 4.8.0 + mathlib v4.8.0 |
| Public release | `releases/v0.2.0/` |

## Quick start

**Linux and macOS:**

```bash
make setup
make test
make validate-examples
make demo
```

**Windows (PowerShell):**

```powershell
.\scripts\dev.ps1 setup
.\scripts\dev.ps1 test
.\scripts\dev.ps1 validate-examples
.\scripts\dev.ps1 demo
```

The offline demo runs the full artifact pipeline on both reference examples without OpenAI or network access. See [docs/DEMO.md](docs/DEMO.md).

Optional model dependencies:

```bash
make setup-models
```

Live extraction with OpenAI (requires `OPENAI_API_KEY`):

```bash
make demo-live
```

On Windows:

```powershell
.\scripts\dev.ps1 demo-live
```

## What is implemented

- Pydantic artifact schemas: source documents, theorem/proof units, readiness reports, proof graphs, Atlas records, and LeanTask packages.
- Semantic validators for graph edges, readiness-report paths, Atlas evidence, and LeanTask requirements.
- Deterministic LaTeX ingestion with source-span preservation.
- OpenAI Responses provider behind a structured model-client boundary.
- Readiness, ProofGraph, Atlas, and LeanTask extraction orchestration with post-extraction validation.
- mathlib declaration index v0 and multi-dimensional alignment service (candidate vs confirmed).
- LeanTask renderer (L0 planning, L1/L2 Lean skeletons) and local `lake env lean` checking.
- Corpus catalog ingestion, release-mode filtering, and shareable export.
- ReadinessBench Bronze/Silver/Gold layout, manifest validation, and evaluation runner.
- External review workflow: reviewer docs, submission template, usefulness rubric, and Gold changelog.
- FastAPI review backend (`apps/api/`) and minimal static review UI (`apps/review-ui/`).
- Public ReadinessBench and Atlas JSONL export with licensing leak tests.
- Docker Compose stack with Redis/RQ async jobs (`docs/DOCKER.md`).
- End-to-end offline and live demos for both reference examples.

## End-to-end demo

```bash
make demo
make demo-finite-tree
make demo-category-theory
```

See [docs/DEMO.md](docs/DEMO.md) for stage-by-stage walkthrough, expected outputs, and environment variables.

## Core commands

Validate reference example stacks:

```bash
make validate-examples
```

Export public JSON Schemas:

```bash
make export-schemas
```

Corpus ingestion:

```bash
make ingest-corpus
make export-corpus-shareable
```

ReadinessBench:

```bash
make validate-readinessbench
make run-readinessbench PREDICTIONS_DIR=tests/fixtures/readinessbench_predictions
```

Public exports:

```bash
make export-public-benchmark
make export-public-atlas
```

Review API and UI:

```bash
make setup-api
make run-api
make run-review-ui
```

Open `http://127.0.0.1:8080`. See [apps/review-ui/README.md](apps/review-ui/README.md) and [docs/PUBLIC_RELEASE.md](docs/PUBLIC_RELEASE.md).

Documentation site:

```bash
make docs
```

On Windows, use `.\scripts\dev.ps1 <target>` for any Make target listed above. See [scripts/dev.ps1](scripts/dev.ps1).

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/index.md](docs/index.md) | Documentation home (MkDocs) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Pipeline and module map |
| [docs/DEMO.md](docs/DEMO.md) | End-to-end demo walkthrough |
| [docs/PUBLIC_RELEASE.md](docs/PUBLIC_RELEASE.md) | Public benchmark and Atlas exports |
| [docs/TECHNICAL_REPORT.md](docs/TECHNICAL_REPORT.md) | Wave 6 release summary |
| [docs/DOCKER.md](docs/DOCKER.md) | Docker Compose and async jobs |
| [docs/CORPUS_GOVERNANCE.md](docs/CORPUS_GOVERNANCE.md) | Source catalog and release modes |
| [docs/OPENAI_USAGE.md](docs/OPENAI_USAGE.md) | Model-call conventions |
| [docs/review/REVIEWER_GUIDE.md](docs/review/REVIEWER_GUIDE.md) | External review workflow |
| [benchmarks/readinessbench/README.md](benchmarks/readinessbench/README.md) | ReadinessBench tiers and scoring |
| [lean/README.md](lean/README.md) | Pinned Lean project setup |
| [docs/ENGINEERING_HANDOFF.md](docs/ENGINEERING_HANDOFF.md) | Engineer takeover guide |
| [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) | Long-term technical plan |
| [docs/NEXT_SPRINTS.md](docs/NEXT_SPRINTS.md) | Completed sprints and optional follow-on work |

## Citation

If you use ReadinessBench or the Formalization Readiness Engine artifacts in research, cite the repository and release manifest:

```text
Formalization Readiness Engine (v0.2.0).
https://github.com/fraware/formalization-readiness-engine
Release manifest: releases/v0.2.0/manifest.json
```

## Development rule

Do not bypass the artifact pipeline. Every new feature should create, validate, render, evaluate, or document one of the project artifacts. Model outputs should never be written directly into trusted benchmark data without validation and review.
