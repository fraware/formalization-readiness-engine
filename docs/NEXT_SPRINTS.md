# Next Engineering Sprints

This document gives the recommended PR sequence after the initial handoff.

## Sprint 1: first live extraction loop

Goal: run the first live model extraction and compare it against the hand-authored finite-tree artifact stack.

Tasks:

1. Install model dependencies with `make setup-models`.
2. Run `extract-report` on `examples/finite_tree/unit.json`.
3. Save the model output under `artifacts/generated/finite_tree/readiness_report.model.json`.
4. Add a validation command or test that loads the generated candidate report.
5. Compare candidate report fields against `examples/finite_tree/readiness_report.json` using `fre_core.evaluation`.
6. Document observed errors in `artifacts/generated/finite_tree/NOTES.md`.

Acceptance criteria:

- candidate report validates as a `ReadinessReport`;
- semantic validation passes;
- evaluation metrics run without manual data reshaping;
- generated output is clearly marked as candidate data.

## Sprint 2: pinned Lean project

Goal: make LeanTask checking real, reproducible, and separate from lightweight Python CI.

Tasks:

1. Add a `lean/` Lake project.
2. Pin Lean and mathlib versions.
3. Add a README inside `lean/` with exact setup commands.
4. Render the finite-tree LeanTask into the project.
5. Run `check-lean` locally.
6. Decide whether generated L1 files should allow `sorry` during scaffold checks.
7. Add an optional GitHub Actions workflow for Lean checks, manual dispatch only at first.

Acceptance criteria:

- `lake update` and `lake build` are documented;
- `check-lean` can run on one rendered LeanTask file;
- the Lean workflow does not slow down normal Python CI unless explicitly enabled.

## Sprint 3: corpus catalog file and ingestion workflow

**Status:** Complete on `engineering-sprint3-corpus-catalog`.

Goal: make source governance concrete instead of only library-level.

Tasks:

1. Add `corpus/catalog.json` with one finite-tree example source.
2. Add a small raw LaTeX source under a permitted example path.
3. Add a CLI command or script that parses the catalog source into units.
4. Validate unit source IDs against the catalog.
5. Add a shareable export example where text is retained or stripped according to release mode.

Delivered:

- `corpus/catalog.json` and `corpus/sources/finite_tree.tex`
- `ingest-catalog` and `export-shareable-units` CLI commands
- `ingest_catalog`, `export_shareable_units`, and catalog path helpers in `corpus.py`
- `examples/corpus_shareable/` with full-text and metadata-only export fixtures
- `tests/test_corpus_ingestion.py` covering ingest, validation, release modes, and source spans
- `make ingest-corpus`, `make export-corpus-shareable`, and matching `scripts/dev.ps1` targets

Acceptance criteria:

- every generated unit points to a catalog source;
- release mode is tested with at least one full-text and one metadata-only fixture;
- source-span preservation is preserved through ingestion.

## Sprint 4: ProofGraph and Atlas extraction scaffolds

**Status:** Complete on `engineering-sprint4-graph-atlas-extraction`.

Goal: extend extraction beyond readiness reports while preserving the artifact-first design.

Tasks:

1. Add prompt builders for `ProofGraph` and `AtlasRecord` extraction.
2. Keep provider code behind the structured model-client boundary.
3. Add fake-client unit tests.
4. Add semantic validation after extraction.
5. Generate candidate proof-graph and Atlas artifacts for the finite-tree example.

Delivered:

- `extract_proofgraph.py` and `extract_atlas.py` orchestration modules with prompt builders
- `extract-proofgraph` and `extract-atlas` CLI commands
- Fake-client tests for prompts, unit_id alignment, and post-extraction validation
- Negative tests rejecting broken graph edges and missing Atlas evidence
- `make extract-finite-tree-proofgraph`, `make extract-finite-tree-atlas`, and matching `scripts/dev.ps1` targets
- Candidate outputs under `artifacts/generated/finite_tree/` (gitignored)

Acceptance criteria:

- model outputs validate through existing validators;
- broken graph edges are rejected;
- Atlas records contain evidence and recommended action;
- generated artifacts remain separate from reviewed examples.

## Sprint 5: mathlib declaration index v0

**Status:** Complete on `engineering-sprint5-mathlib-index`.

Goal: replace free-text theorem-candidate guesses with a reproducible declaration lookup layer.

Tasks:

1. Create a declaration-index schema.
2. Ingest a small static fixture of mathlib declarations relevant to finite trees.
3. Add lexical lookup by declaration name, namespace, and module.
4. Connect lookup results to readiness-report candidate fields.
5. Add tests proving stable ranking for a finite-tree query.

Delivered:

- `DeclarationIndex` and `MathlibDeclaration` schemas with JSON Schema export
- Committed fixture `fixtures/mathlib_declarations/finite_tree_v0.json`
- `mathlib_index.py` with `load_index`, `search`, and `enrich_readiness_candidates`
- `lookup-declarations` and `enrich-report-candidates` CLI commands
- Optional `--enrich-candidates` flag on `extract-report`
- `make lookup-finite-tree-declarations` and matching `scripts/dev.ps1` target
- `tests/test_mathlib_index.py` covering deterministic finite-tree ranking

Acceptance criteria:

- no network call is needed for tests;
- candidate theorem names come from the index fixture;
- ranking is deterministic;
- the index schema can later be populated from a real mathlib export.

## Sprint 6: ReadinessBench gold/silver/bronze layout

Goal: make benchmark tiers explicit.

Tasks:

1. Add `benchmarks/readinessbench/bronze`, `silver`, and `gold` directories.
2. Define what each tier can contain.
3. Add a manifest format for benchmark items.
4. Add evaluation scripts for predicted-vs-gold report pairs.
5. Add CI tests on a tiny fixture.

Acceptance criteria:

- benchmark layout is documented;
- gold reports are clearly reviewed data;
- generated reports are never silently treated as gold;
- evaluation produces deterministic metrics.

## Sprint 7: external-review workflow

Goal: prepare the repo for mathematician and formalizer feedback.

Tasks:

1. Add reviewer instructions for a theorem/proof unit.
2. Add a review form template for readiness reports.
3. Add scoring rubric for external usefulness.
4. Add examples of acceptable and unacceptable edits to generated artifacts.
5. Add a changelog for reviewed gold artifacts.

Acceptance criteria:

- a reviewer can evaluate one unit without reading the codebase;
- review outputs are structured enough to feed ReadinessBench;
- changes to gold artifacts are auditable.
