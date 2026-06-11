# Architecture

This document describes the current Formalization Readiness Engine architecture. For the long-term roadmap, see `IMPLEMENTATION_PLAN.md`. For the next PR sequence, see `NEXT_SPRINTS.md`.

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
        +--> DeclarationIndex lookup (mathlib_index) --> candidate theorem names
        |
        +--> ProofGraph      <-- extract_proofgraph + StructuredModelClient
        +--> AtlasRecord     <-- extract_atlas + StructuredModelClient
        |
        v
LeanTaskPackage
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
| `fixtures/mathlib_declarations/` | Committed mathlib declaration index fixtures (v0 lexical lookup) |
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
  mathlib_index.py           Declaration index load, lexical search, candidate enrichment
  benchmark.py               ReadinessBench manifest validation and evaluation runner
  evaluation.py              ReadinessBench metrics
  cli.py                     Typer CLI entry point
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
