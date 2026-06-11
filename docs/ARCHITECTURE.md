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
