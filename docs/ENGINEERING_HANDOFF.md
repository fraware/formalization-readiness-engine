# Engineering Handoff

This document is the takeover guide for engineers continuing the Formalization Readiness Engine.

## Project invariant

The system is artifact-first. Every pipeline step should produce, validate, render, evaluate, or document a typed artifact. Model outputs are candidate artifacts until they pass schema validation, semantic validation, and human review.

The current implementation should be treated as a foundation for the first working benchmark pipeline. It should not be presented as an end-to-end theorem-proving system.

## Reference examples

Two hand-authored artifact stacks validate under `make validate-examples`:

- `examples/finite_tree/` — finite-tree edge-count theorem (graph theory)
- `examples/category_theory_pullback/` — pullback transport along a categorical equivalence

The category-theory stack includes L0 and L1 LeanTask packages, a corpus LaTeX source at `corpus/sources/category_theory_pullback.tex`, and a mathlib fixture at `fixtures/mathlib_declarations/category_theory_v0.json`. It is examples-only until promoted through the review workflow and ReadinessBench manifest.

## Current branch state

`main` contains all accepted work from the initial engineering sprint. The temporary branches below were used for focused PRs and have already been squash-merged into `main`:

- `engineering-core-validation`
- `engineering-schema-export`
- `engineering-latex-ingestion`
- `engineering-leantask-renderer`
- `engineering-corpus-catalog`
- `engineering-lean-check-runner`
- `engineering-readinessbench-metrics`

If these branches are still visible on GitHub, they can be deleted after confirming `main` is current. See `docs/BRANCH_CLEANUP.md`.

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

### `leantask_renderer.py`

Renders LeanTask packages into Lean files. L0 tasks remain documentation-only. L1/L2 tasks emit theorem skeletons with imports, hypotheses, formal target, and `sorry`.

The renderer preserves Lean typeclass syntax such as `[Fintype V]`.

### `lean_runner.py`

Provides a lightweight local runner for checking Lean files through `lake env lean`. CI mocks this boundary. Full Lean/mathlib checking should run locally or in a heavier CI job once a pinned Lake project exists.

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

## Current tests

Run:

```bash
make setup
make test
make validate-examples
```

The test suite covers:

- schema loading;
- semantic artifact validation;
- broken proof-graph rejection;
- JSON Schema export;
- deterministic LaTeX ingestion;
- structured extraction orchestration with a fake model client (`tests/test_extraction.py`, `tests/test_extract_proofgraph.py`, `tests/test_extract_atlas.py`, `tests/test_extract_leantask.py`);
- LeanTask rendering;
- Lean runner command construction;
- corpus release-mode checks;
- corpus catalog ingestion, source-id validation, and shareable export (`tests/test_corpus_ingestion.py`);
- mathlib declaration index load, deterministic search, and candidate enrichment (`tests/test_mathlib_index.py`);
- ReadinessBench metrics;
- ReadinessBench manifest validation and deterministic benchmark evaluation (`tests/test_benchmark.py`);
- external review submission and Gold changelog validation (`tests/test_review_workflow.py`).

## First engineer takeover checklist

1. Pull latest `main`.
2. Delete merged engineering branches or leave them untouched if branch deletion is restricted.
3. Run `make setup`, `make test`, and `make validate-examples`.
4. Run `make export-schemas` and inspect generated schemas.
5. Run one live model extraction with an API key and save the output under `artifacts/generated/...`.
6. Review the model output manually before using it as benchmark data.
7. Set up or confirm the local `lean/` Lake project before running `check-lean`.
8. Start the next PR from `main` using the sequence in `docs/NEXT_SPRINTS.md`.

## Engineering discipline

Use small PRs. Each PR should add one capability and one set of tests. Avoid mixing extraction, scoring, Lean integration, and corpus policy changes in the same PR.

Do not add unreviewed generated artifacts to gold benchmark directories. Candidate model outputs should live in a generated or scratch location until reviewed.
