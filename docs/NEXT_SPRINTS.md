# Next Engineering Sprints

This document records completed engineering sprints and optional follow-on work after the June 2026 public release.

**Status:** Sprints 1–7, category-theory example, LeanTask generation, Phase 5–6, E2E demo, and Waves 0–6 scale-up are complete on `main`. New contributors should branch from `main` and pick items from [Optional follow-on work](#optional-follow-on-work) below.

## Subsystem maturity (June 2026)

Honest progress snapshot for external readers. Percentages are engineering estimates, not product KPIs.

| Subsystem | Maturity | Next epic |
|-----------|----------|-----------|
| LaTeX ingestion | ~30% | Controlled notes only; add `\newtheorem` discovery, labels/refs, macros, multi-proof in `ingestion_v1` |
| OpenAI extraction | ~35–40% | Harness + two live reference runs; expand into benchmark-wide live eval campaign ([`docs/evidence/live_extraction_v0.2/`](evidence/live_extraction_v0.2/)) |
| mathlib alignment | ~30–35% | Fixture lexical + embedding sidecars; mathlib-scale index and elaboration-aware matching |
| LeanTask | ~30% | `sorry` skeletons typecheck under mathlib v4.8.0; proof-completion loop + CI gate |
| ReadinessBench | ~35% | Repo fixtures as gold; external expert review workflow and richer metrics beyond string overlap |
| Atlas | Scaffold | Populate from reviewed exports, not generated-only |
| API / review UI | ~20–25% | Demo API and static review UI; auth, reviewer identity, promotion CLI |
| Docker | ~25% | Compose files present; `docker compose build && up` smoke test in CI |

## Sprint 1: first live extraction loop

**Status:** Complete on `main`.

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

**Status:** Complete on `main`.

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

**Status:** Complete on `engineering-sprint6-readinessbench-tiers`.

Goal: make benchmark tiers explicit.

Tasks:

1. Add `benchmarks/readinessbench/bronze`, `silver`, and `gold` directories.
2. Define what each tier can contain.
3. Add a manifest format for benchmark items.
4. Add evaluation scripts for predicted-vs-gold report pairs.
5. Add CI tests on a tiny fixture.

Delivered:

- `benchmarks/readinessbench/` tier layout with gold, silver, and bronze finite-tree fixtures
- `BenchmarkManifest`, `BenchmarkItem`, and `BenchmarkEvaluationReport` schemas with JSON Schema export
- `benchmark.py` with manifest validation, tier invariants, and deterministic evaluation runner
- `validate-readinessbench` and `run-readinessbench` CLI commands
- `tests/test_benchmark.py` and prediction fixture under `tests/fixtures/readinessbench_predictions/`
- `make validate-readinessbench`, `make run-readinessbench`, and matching `scripts/dev.ps1` targets

Acceptance criteria:

- benchmark layout is documented;
- gold reports are clearly reviewed data;
- generated reports are never silently treated as gold;
- evaluation produces deterministic metrics.

## Sprint 7: external-review workflow

**Status:** Complete on `engineering-sprint7-review-workflow`.

Goal: prepare the repo for mathematician and formalizer feedback.

Tasks:

1. Add reviewer instructions for a theorem/proof unit.
2. Add a review form template for readiness reports.
3. Add scoring rubric for external usefulness.
4. Add examples of acceptable and unacceptable edits to generated artifacts.
5. Add a changelog for reviewed gold artifacts.

Delivered:

- `docs/review/` reviewer guide, review form, usefulness rubric, and edit examples
- `docs/review/templates/readiness_report_review.json` structured submission template
- `ReadinessReportReviewSubmission` and `GoldArtifactChangelogEntry` schemas with JSON Schema export
- `review_workflow.py` with submission and changelog validation
- `validate-review-submission` and `validate-gold-changelog` CLI commands
- `benchmarks/readinessbench/gold/CHANGELOG.md` and `gold/changelog.jsonl` auditable Gold change log
- `tests/test_review_workflow.py` covering submission template and changelog validation

Acceptance criteria:

- a reviewer can evaluate one unit without reading the codebase;
- review outputs are structured enough to feed ReadinessBench;
- changes to gold artifacts are auditable.

## Post-Sprint 7: category-theory reference example

**Status:** Complete on `engineering-category-theory-example`.

Goal: add the second Phase 0 hand-authored reference stack for pullback transport along a categorical equivalence.

Delivered:

- `examples/category_theory_pullback/` with unit, readiness report, proof graph, Atlas record, L0/L1 LeanTask packages
- `corpus/sources/category_theory_pullback.tex` and catalog entry in `corpus/catalog.json`
- `fixtures/mathlib_declarations/category_theory_v0.json` for deterministic lookup tests
- `make validate-examples` and CI validate both reference directories
- tests in `tests/test_schemas.py`, `tests/test_mathlib_index.py`, and `tests/test_corpus_ingestion.py`

Acceptance criteria:

- all category-theory artifacts validate with semantic checks;
- `unit_id` is consistent across the stack;
- example remains examples-only until reviewed for ReadinessBench promotion.

## Post-Sprint: LeanTask generation

**Status:** Complete on `engineering-leantask-generation`.

Goal: connect readiness reports to formalization action through model-assisted LeanTask package generation.

Tasks:

1. Add prompt builder and orchestration for `LeanTaskPackage` from `TheoremProofUnit` + `ReadinessReport`.
2. Keep provider code behind the structured model-client boundary.
3. Add fake-client unit tests and L1 formal-target validation.
4. Add `generate-leantask` CLI and Makefile/dev.ps1 targets for both reference examples.
5. Document the extract-report → generate-leantask → render → check-lean workflow.

Delivered:

- `extract_leantask.py` with `LEANTASK_GENERATION_INSTRUCTIONS`, `build_leantask_prompt`, `extract_leantask_package`, and `enrich_imports_from_index`
- `generate-leantask` CLI command with optional `--level` and `--enrich-imports`
- `make generate-finite-tree-leantask`, `make generate-category-theory-leantask`, and matching `scripts/dev.ps1` targets
- `tests/test_extract_leantask.py` covering prompts, unit_id alignment, L1 validation, import enrichment, and structural gold comparison
- Candidate outputs under `artifacts/generated/<example>/leantask.model.json` (gitignored)

Acceptance criteria:

- model outputs validate through `validate_leantask_package`;
- L1 packages without `formal_target` are rejected;
- generated artifacts remain separate from reviewed examples;
- all existing tests pass.

## Optional follow-on work

These items are not blockers for the v0.2.0 public release. They extend coverage, reviewer tooling, or deployment depth.

### Annotation workflow in review UI

Goal: let reviewers produce Silver and Gold artifacts through the web interface instead of manual JSON editing.

Tasks:

1. Add versioned reviewer edits with audit trail.
2. Wire Bronze/Silver/Gold tagging into the review UI.
3. Connect submission validation to benchmark promotion CLI.

### L2 LeanTask for selected Gold examples

Goal: move selected gold items from L1 statement scaffolds to partial proof skeletons without `sorry`.

Tasks:

1. Define L2 promotion criteria in `docs/review/`.
2. Add gold-tier L2 LeanTask fixtures and Lean check targets.
3. Document proof-completion policy in `lean/README.md`.

### Baseline comparison harness (Wave 3)

Goal: replace the `run_baselines` job stub with a reproducible multi-baseline evaluation loop.

Tasks:

1. Implement direct extraction, retrieval-augmented, and ablated baselines.
2. Aggregate errors with `docs/ERROR_TAXONOMY.md` categories.
3. Add CI fixtures for deterministic baseline reports.

### Category-theory ReadinessBench promotion

Goal: promote `examples/category_theory_pullback/` through external review into the gold tier.

Tasks:

1. Complete external review per `docs/review/REVIEWER_GUIDE.md`.
2. Copy reviewed artifacts into `benchmarks/readinessbench/gold/`.
3. Update `manifest.json` and Gold changelog.

### PostgreSQL and object storage

Goal: move job metadata and artifact storage off SQLite/local disk for multi-user deployments.

Tasks:

1. Add PostgreSQL service to Docker Compose.
2. Migrate `FRE_JOBS_DB` schema.
3. Document backup and retention policy.

### Technical report automation

Goal: generate release notes and evaluation summaries from manifest and cluster artifacts.

Tasks:

1. Wire `build-release-manifest` into release CI.
2. Add evaluator-facing report templates under `docs/`.
3. Version reports alongside `releases/<version>/`.
