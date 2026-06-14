# Architecture

This document describes the Formalization Readiness Engine architecture as implemented on `main` (June 2026 public release). For the long-term roadmap, see `IMPLEMENTATION_PLAN.md`. For completed sprints and optional follow-on work, see `NEXT_SPRINTS.md`.

## Design principle

The system is a compiler-like front end for informal mathematics. Every stage produces a versioned, typed artifact that can be validated, reviewed, scored, and exported. Model outputs are candidates until schema validation, semantic validation, and human review pass.

## Pipeline

```text
SourceDocument (corpus catalog)
        |
        v
TheoremProofUnit  <-- latex_ingestion + ingest_catalog
        |
        v
ReadinessReport   <-- extraction + StructuredModelClient
        |
        +--> DeclarationIndex lookup (mathlib_index / mathlib_alignment) --> candidate theorem names
        |
        +--> ProofGraph      <-- extract_proofgraph + StructuredModelClient
        +--> AtlasRecord     <-- extract_atlas + StructuredModelClient
        |
        v
LeanTaskPackage   <-- extract_leantask + StructuredModelClient (+ optional mathlib import enrichment)
        |
        v
.lean skeleton    <-- leantask_renderer
        |
        v
Lean check        <-- lean_runner
        |
        v
ReadinessBench    <-- evaluation
```

## Corpus layout

| Path | Purpose |
|------|---------|
| `corpus/catalog.json` | Committed source catalog with license and release metadata |
| `corpus/sources/` | Permitted LaTeX inputs referenced by the catalog |
| `fixtures/mathlib_declarations/` | Committed mathlib declaration index fixtures (v0 lexical lookup; finite-tree and category-theory) |
| `examples/category_theory_pullback/` | Hand-authored category-theory reference artifacts (pullback transport along equivalence) |
| `benchmarks/readinessbench/` | ReadinessBench manifest and Bronze/Silver/Gold readiness-report fixtures |
| `examples/corpus_shareable/` | Shareable export demo with full-text and metadata-only fixtures |

## Key modules

```text
packages/fre_core/src/fre_core/
  schemas.py                 Artifact contracts (Pydantic)
  validation.py              Semantic validators and JSON loaders
  latex_ingestion.py         LaTeX -> TheoremProofUnit
  corpus.py                  Catalog load, ingest, validate, shareable export
  extraction.py              ReadinessReport orchestration
  extract_proofgraph.py      ProofGraph orchestration
  extract_atlas.py           AtlasRecord orchestration
  extract_leantask.py        LeanTaskPackage orchestration from unit + readiness report
  mathlib_index.py           Declaration index load, lexical search, candidate enrichment
  mathlib_alignment.py       Multi-dimensional alignment service (candidate vs confirmed)
  public_export.py           Public ReadinessBench and Atlas JSONL export
  benchmark.py               ReadinessBench manifest validation and evaluation runner
  review_workflow.py         External review submission and Gold changelog validation
  evaluation.py              ReadinessBench metrics
  cli.py                     Typer CLI entry point

apps/
  api/main.py                FastAPI validation and alignment endpoints
  review-ui/                 Minimal static review interface
```

## Sprint 3 ingestion workflow

1. Load `corpus/catalog.json`.
2. Resolve each `SourceDocument.path` relative to the repository root.
3. Parse `.tex` sources into `TheoremProofUnit` artifacts with source spans.
4. Validate that every unit `source_id` appears in the catalog.
5. Export shareable units with text retained or stripped according to `release_mode`.

Commands:

```bash
make ingest-corpus
make export-corpus-shareable
```

Or on Windows:

```powershell
.\scripts\dev.ps1 ingest-corpus
.\scripts\dev.ps1 export-corpus-shareable
```

## Sprint 5 mathlib index workflow

1. Load a committed declaration index fixture (for example `fixtures/mathlib_declarations/finite_tree_v0.json`).
2. Build a lexical query from a unit or readiness report.
3. Search the index for ranked candidate theorem names (Bronze candidates only).
4. Optionally enrich `existing_theorem_candidates` on a readiness report.

Commands:

```bash
make lookup-finite-tree-declarations
PYTHONPATH=packages/fre_core/src python -m fre_core.cli lookup-declarations --query "finite tree edge card"
PYTHONPATH=packages/fre_core/src python -m fre_core.cli enrich-report-candidates \
  examples/finite_tree/readiness_report.json \
  artifacts/generated/finite_tree/readiness_report.enriched.json
```

Or on Windows:

```powershell
.\scripts\dev.ps1 lookup-finite-tree-declarations
```

## Sprint 6 ReadinessBench workflow

1. Load `benchmarks/readinessbench/manifest.json`.
2. Validate tier invariants: Gold requires `expert_reviewed` or `human_reviewed`; Bronze requires `candidate` or `machine_validated`.
3. Reject manifest paths under `artifacts/generated/`.
4. Score predicted readiness reports against Gold items only.

Commands:

```bash
make validate-readinessbench
make run-readinessbench PREDICTIONS_DIR=tests/fixtures/readinessbench_predictions
```

Or on Windows:

```powershell
.\scripts\dev.ps1 validate-readinessbench
.\scripts\dev.ps1 run-readinessbench -PredictionsDir tests/fixtures/readinessbench_predictions
```

See `benchmarks/readinessbench/README.md` for tier definitions and promotion rules.

## Sprint 7 external review workflow

1. Reviewer reads `docs/review/REVIEWER_GUIDE.md` and the unit JSON artifacts only.
2. Reviewer completes `docs/review/READINESS_REPORT_REVIEW_FORM.md` and fills `docs/review/templates/readiness_report_review.json`.
3. Reviewer scores external usefulness using `docs/review/USEFULNESS_RUBRIC.md`.
4. Corrected reports are promoted to Silver or Gold tier directories; Gold edits are logged in `benchmarks/readinessbench/gold/changelog.jsonl` and `CHANGELOG.md`.
5. Validate submissions with `validate-review-submission` and the Gold changelog with `validate-gold-changelog`.

Commands:

```bash
PYTHONPATH=packages/fre_core/src python -m fre_core.cli validate-review-submission \
  docs/review/templates/readiness_report_review.json
PYTHONPATH=packages/fre_core/src python -m fre_core.cli validate-gold-changelog
```

Or on Windows:

```powershell
$env:PYTHONPATH = "packages/fre_core/src"
python -m fre_core.cli validate-review-submission docs/review/templates/readiness_report_review.json
python -m fre_core.cli validate-gold-changelog
```

## LeanTask generation workflow

1. Extract or load a readiness report for a theorem/proof unit (optionally enrich theorem candidates with `--enrich-candidates` on `extract-report`).
2. Generate a candidate LeanTask package with `generate-leantask`.
3. Render the package with `render-leantask`.
4. Optionally typecheck L1 skeletons with `check-lean`.

Commands:

```bash
make generate-finite-tree-leantask
make generate-category-theory-leantask
OPENAI_API_KEY=... PYTHONPATH=packages/fre_core/src python -m fre_core.cli generate-leantask \
  examples/finite_tree/unit.json \
  examples/finite_tree/readiness_report.json \
  artifacts/generated/finite_tree/leantask.model.json \
  --level L0
```

Or on Windows:

```powershell
.\scripts\dev.ps1 generate-finite-tree-leantask
.\scripts\dev.ps1 generate-category-theory-leantask
```

Candidate outputs are written under `artifacts/generated/`. Reviewed gold artifacts remain under `examples/`.

## Phase 5 review API workflow

1. Start the FastAPI backend with `make run-api`.
2. Serve the minimal review UI with `make run-review-ui`.
3. Load example artifact metadata from `GET /examples/{name}`.
4. Validate readiness reports and review submissions through artifact-first POST endpoints.
5. Propose mathlib alignment candidates with `POST /align/readiness-report` (confirmed alignment requires explicit reviewer flags).

See `apps/review-ui/README.md` and `docs/PUBLIC_RELEASE.md`.

## Phase 6 public export workflow

1. Export ReadinessBench tiers with `make export-public-benchmark`.
2. Export curated Atlas records with `make export-public-atlas`.
3. Optional corpus catalog paths strip restricted source text via `make_shareable_units`.
4. CI runs licensing leak tests on metadata-only sources.

Commands:

```bash
make export-public-benchmark
make export-public-atlas
PYTHONPATH=packages/fre_core/src:. python -m fre_core.cli align-readiness-report \
  examples/finite_tree/readiness_report.json \
  artifacts/generated/finite_tree/alignment.json \
  --unit-path examples/finite_tree/unit.json
```

## mathlib alignment service

The alignment service extends Sprint 5 lexical lookup with namespace, module-path, and declaration-kind dimensions. `AlignmentResult` separates `candidates` from `confirmed`; retrieval never auto-promotes to confirmed status.
