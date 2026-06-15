# Engineering Handoff

This document is the takeover guide for engineers continuing the Formalization Readiness Engine after the June 2026 public release.

## Project invariant

The system is artifact-first. Every pipeline step should produce, validate, render, evaluate, or document a typed artifact. Model outputs are candidate artifacts until they pass schema validation, semantic validation, and human review.

The current implementation is a working benchmark foundation. It should not be presented as an end-to-end theorem-proving system.

## Release state

All Waves 0–6 work is merged on `main`, including:

- Sprints 1–7 (extraction, Lean pins, corpus, ProofGraph/Atlas, mathlib index, ReadinessBench tiers, external review)
- Category-theory reference example and LeanTask generation
- Phase 5 review API/UI and Phase 6 public export
- End-to-end offline and live demos
- Docker Compose with Redis/RQ async jobs

Temporary `engineering-*` sprint branches were squash-merged and removed from the remote. See `docs/ENGINEERING_BRANCH_STATUS.md` for the historical merge record.

## Reference examples

Two hand-authored artifact stacks validate under `make validate-examples`:

- `examples/finite_tree/` — finite-tree edge-count theorem (graph theory)
- `examples/category_theory_pullback/` — pullback transport along a categorical equivalence

The category-theory stack includes L0 and L1 LeanTask packages, a corpus LaTeX source at `corpus/sources/category_theory_pullback.tex`, and a mathlib fixture at `fixtures/mathlib_declarations/category_theory_v0.json`. It is examples-only until promoted through the review workflow and ReadinessBench manifest.

## Benchmark and corpus scale

| Artifact | Count |
|----------|-------|
| ReadinessBench manifest items | 43 (11 gold, 1 silver, 31 bronze) |
| Corpus ingested units | 30 from 5 catalog sources |
| Unit tests | 352 |

Gold items are evaluated truth. Bronze items hold corpus-scale candidate units. Silver preserves the promotion workflow example.

## Implemented modules

### `packages/fre_core/src/fre_core/schemas.py`

Defines the public artifact contracts:

- `SourceDocument`
- `TheoremProofUnit`
- `ReadinessReport`
- `ProofGraph`
- `AtlasRecord`
- `LeanTaskPackage`
- `DeclarationIndex` and `MathlibDeclaration` (mathlib lookup index)

These classes are the center of the repository. Add fields only when the new field is required by the formalization-readiness spec or by a reviewed benchmark need.

### `validation.py`

Adds semantic checks that Pydantic alone cannot enforce:

- proof-graph edge endpoints must refer to existing nodes;
- readiness reports must include a next action and at least one formalization path;
- Atlas records must include evidence and an action;
- L1/L2 LeanTasks require formal targets.

### `schema_exports.py`

Exports public JSON Schemas for downstream tools and reviewers.

### `latex_ingestion.py`

Parses theorem-like LaTeX environments into theorem/proof units. It currently supports deterministic extraction of:

- theorem;
- lemma;
- proposition;
- corollary.

It also pairs an immediately following proof block and preserves character spans for statement and proof text.

### `model_client.py`, `openai_responses_provider.py`, `extraction.py`, `extract_proofgraph.py`, `extract_atlas.py`, `extract_leantask.py`, and `mathlib_index.py`

Keep model calls behind an interface. The current OpenAI provider uses structured output parsing and returns Pydantic objects. Engineers should keep provider-specific code isolated in provider modules.

Extraction orchestration modules build prompts, call the structured model client, align `unit_id` with the source unit, and run semantic validation before returning artifacts.

`extract_leantask.py` generates `LeanTaskPackage` artifacts from a `TheoremProofUnit` and `ReadinessReport`. L0 is the default planning level; L1 requires a `formal_target`. Optional `enrich_imports_from_index` appends mathlib module paths from deterministic index lookup.

`mathlib_index.py` provides deterministic lexical lookup over committed declaration-index fixtures. Index hits are candidate alignments only; Silver and Gold records require human review. Use `--enrich-candidates` on `extract-report` or `enrich-report-candidates` to replace free-text theorem guesses with index-backed names.

`mathlib_alignment.py` extends the index into a proper alignment service with namespace, module-path, and declaration-kind search dimensions. `AlignmentResult` separates `candidates` from `confirmed`; confirmed alignment requires explicit reviewer flags and is never auto-promoted. CLI commands: `align-declarations` and `align-readiness-report`.

`public_export.py` exports ReadinessBench and Atlas records as public JSONL with optional corpus release-mode filtering. CLI commands: `export-public-benchmark`, `export-public-atlas`, and `check-licensing-leak`. See `docs/PUBLIC_RELEASE.md`.

`apps/api/main.py` exposes artifact-first FastAPI endpoints for health checks, example metadata, readiness-report validation, review-submission validation, alignment, and async RQ jobs. `apps/review-ui/` is a minimal static review surface for Phase 5.

### `leantask_renderer.py`

Renders LeanTask packages into Lean files. L0 tasks remain documentation-only. L1/L2 tasks emit theorem skeletons with imports, hypotheses, formal target, and `sorry`.

The renderer preserves Lean typeclass syntax such as `[Fintype V]`.

### `lean_runner.py`

Provides a lightweight local runner for checking Lean files through `lake env lean`. CI mocks this boundary. Full Lean/mathlib checking runs locally or in the optional `.github/workflows/lean.yml` workflow (`workflow_dispatch` only).

### `corpus.py`

Provides corpus catalog loading, LaTeX ingestion from catalog sources, source-id validation, and release-mode filtering for shareable exports. CLI commands: `ingest-catalog` and `export-shareable-units`. See `corpus/catalog.json`, `examples/corpus_shareable/`, and `docs/ARCHITECTURE.md`.

### `evaluation.py` and `benchmark.py`

Provides deterministic ReadinessBench metrics for comparing predicted readiness reports to reviewed gold reports. The first metric layer scores:

- existing-theorem candidates;
- constructive path items;
- blockers.

`benchmark.py` loads the ReadinessBench manifest, enforces Bronze/Silver/Gold tier invariants, rejects `artifacts/generated/` paths, and runs predicted-vs-gold evaluation through the CLI commands `validate-readinessbench` and `run-readinessbench`.

### `review_workflow.py`

Validates structured external review submissions and Gold artifact changelog entries. Reviewers produce JSON submissions mapped to `ReadinessReportReviewSubmission`; Gold changes are logged in `benchmarks/readinessbench/gold/changelog.jsonl` and `CHANGELOG.md`. CLI commands: `validate-review-submission` and `validate-gold-changelog`. See `docs/review/`.

## Verification commands

Primary CI-equivalent check (Python tests, example validation, lint):

```bash
make check
```

On Windows without GNU Make:

```powershell
.\scripts\dev.ps1 check
```

Offline demo (both reference examples; Lean check skipped in CI):

```bash
make demo
```

ReadinessBench manifest validation:

```bash
make validate-readinessbench
```

Lean pin setup and finite-tree scaffold check (local; requires elan + `lake`):

```bash
make setup-lean
make check-lean-finite-tree
```

Optional Lean workflow: `.github/workflows/lean.yml` (`workflow_dispatch` only).

Docker Compose stack:

```bash
docker compose up --build
```

See `docs/DOCKER.md`.

## Current tests

Run:

```bash
make setup
make check
```

The test suite (352 tests) covers:

- schema loading;
- semantic artifact validation;
- broken proof-graph rejection;
- JSON Schema export;
- deterministic LaTeX ingestion;
- structured extraction orchestration with a fake model client;
- LeanTask rendering;
- Lean runner command construction;
- corpus release-mode checks;
- corpus catalog ingestion, source-id validation, and shareable export;
- mathlib declaration index load, deterministic search, and candidate enrichment;
- ReadinessBench metrics;
- ReadinessBench manifest validation and deterministic benchmark evaluation;
- external review submission and Gold changelog validation;
- mathlib alignment service and deterministic ranking;
- FastAPI review endpoints and async job API;
- public export and licensing leak tests;
- pinned Lean project smoke tests;
- end-to-end demo orchestration.

## Engineer takeover checklist

1. Pull latest `main`.
2. Run `make setup` and `make check` (or `.\scripts\dev.ps1 check` on Windows).
3. Run `make demo` to confirm the offline pipeline on both reference examples.
4. Run `make export-schemas` and inspect generated schemas.
5. Run one live model extraction with an API key and save output under `artifacts/generated/...`.
6. Review model output manually before using it as benchmark data.
7. Set up the local `lean/` Lake project before running `check-lean` (see `lean/README.md`).
8. Read `docs/NEXT_SPRINTS.md` for optional follow-on work (annotation UI, L2 LeanTasks, baseline harness, PostgreSQL).

## Engineering discipline

Use small PRs. Each PR should add one capability and one set of tests. Avoid mixing extraction, scoring, Lean integration, and corpus policy changes in the same PR.

Do not add unreviewed generated artifacts to gold benchmark directories. Candidate model outputs should live in a generated or scratch location until reviewed.
