# Formalization Readiness Engine

The Formalization Readiness Engine is an artifact-first system for turning mathematical source material into reviewed formalization-readiness artifacts before any Lean-facing work is treated as reliable.

The repository is organized around a conservative pipeline:

1. source catalog and license metadata;
2. deterministic theorem/proof-unit ingestion;
3. schema-constrained readiness extraction;
4. semantic validation of every artifact;
5. proof-graph, Atlas, and LeanTask artifacts;
6. Lean skeleton rendering and optional local Lean checking;
7. ReadinessBench comparison against reviewed gold reports.

The current implementation is an engineering foundation, not a claim that the system can prove mathematical theorems end to end. Model outputs remain candidate artifacts until they pass schema validation, semantic validation, and human review.

## Current status

Implemented and merged on `main`:

- Pydantic artifact schemas for source documents, theorem/proof units, readiness reports, proof graphs, Atlas records, and LeanTask packages.
- Semantic validators for graph edges, readiness-report paths, Atlas evidence, and LeanTask-level requirements.
- CLI validation commands for individual artifacts and complete example directories.
- JSON Schema export for public artifact contracts.
- Deterministic LaTeX ingestion for theorem-like environments and immediately following proof blocks, with source-span preservation.
- OpenAI Responses provider behind the internal structured model-client boundary.
- Readiness extraction orchestration from `TheoremProofUnit` to `ReadinessReport`.
- LeanTask renderer that emits L0 planning files and L1/L2 Lean skeletons.
- Lean check runner that invokes `lake env lean` locally through a configured Lake project.
- Corpus catalog utilities for source-id validation and release-mode filtering.
- Corpus catalog file (`corpus/catalog.json`), LaTeX source inputs, and `ingest-catalog` / `export-shareable-units` CLI workflow (Sprint 3).
- ReadinessBench precision, recall, F1, and macro-F1 utilities for comparing candidate reports against reviewed reports.

## Setup

```bash
make setup
make test
make validate-examples
```

Optional model dependencies:

```bash
make setup-models
```

## Core commands

Validate the finite-tree example artifact stack:

```bash
PYTHONPATH=packages/fre_core/src python -m fre_core.cli validate-example-dir examples/finite_tree
```

Export public JSON Schemas:

```bash
PYTHONPATH=packages/fre_core/src python -m fre_core.cli export-schemas schemas
```

Parse a LaTeX file into theorem/proof units:

```bash
PYTHONPATH=packages/fre_core/src python -m fre_core.cli ingest-latex source.tex artifacts/units source_001 graph_theory
```

Ingest catalog sources and export shareable units:

```bash
make ingest-corpus
make export-corpus-shareable
```

On Windows:

```powershell
.\scripts\dev.ps1 ingest-corpus
.\scripts\dev.ps1 export-corpus-shareable
```

Run model-based readiness extraction:

```bash
OPENAI_API_KEY=... PYTHONPATH=packages/fre_core/src python -m fre_core.cli extract-report \
  examples/finite_tree/unit.json \
  artifacts/generated/finite_tree/readiness_report.model.json
```

Render a LeanTask into a Lean skeleton:

```bash
PYTHONPATH=packages/fre_core/src python -m fre_core.cli render-leantask \
  examples/finite_tree/leantask.json \
  lean/FRETasks/Generated/FiniteTree.lean
```

Check a rendered Lean file through a local Lake project:

```bash
PYTHONPATH=packages/fre_core/src python -m fre_core.cli check-lean \
  FRETasks/Generated/FiniteTree.lean \
  --project-dir lean
```

## Handoff documents

- `docs/ENGINEERING_HANDOFF.md` gives the current architecture, branch status, and takeover checklist.
- `docs/ARCHITECTURE.md` describes the pipeline and corpus ingestion workflow.
- `docs/NEXT_SPRINTS.md` gives the next PR sequence for engineers.
- `docs/BRANCH_CLEANUP.md` lists the temporary engineering branches that were merged and can be deleted from GitHub if the UI or Git CLI is available.

## Development rule

Do not bypass the artifact pipeline. Every new feature should either create, validate, render, evaluate, or document one of the project artifacts. Model outputs should never be written directly into trusted benchmark data without validation and review.
