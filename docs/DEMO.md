# End-to-end demo

The Formalization Readiness Engine ships a reproducible end-to-end demo that runs the full artifact pipeline on two hand-authored reference examples:

- `examples/finite_tree/` — finite graph theory (edge count in a tree)
- `examples/category_theory_pullback/` — category theory (pullback transport along an equivalence)

The demo is designed for engineers onboarding to the repo and for external users who want to see the pipeline without calling OpenAI.

## Quick start

Offline demo (default, CI-safe, no network):

```bash
make demo
```

On Windows without GNU Make:

```powershell
.\scripts\dev.ps1 demo
```

Run one example only:

```bash
make demo-finite-tree
make demo-category-theory
```

Live extraction (requires `OPENAI_API_KEY`):

```bash
export OPENAI_API_KEY=...
make demo-live
```

Equivalent CLI:

```bash
PYTHONPATH=packages/fre_core/src:. python -m fre_core.cli demo --offline --example all
PYTHONPATH=packages/fre_core/src:. python -m fre_core.cli demo --live --example finite_tree
```

## Modes

### Offline (default)

Uses committed gold artifacts under `examples/` and static mathlib index fixtures under `fixtures/mathlib_declarations/`. No OpenAI calls. Suitable for CI and local smoke checks.

Pipeline per example:

1. **validate-example-dir** — schema and cross-artifact consistency checks on the example stack (`unit.json`, `readiness_report.json`, `proofgraph.json`, `atlas_record.json`, `leantask.json`).
2. **align-readiness-report** — multi-dimensional mathlib alignment against the example-specific index fixture.
3. **enrich-report-candidates** — write an enriched readiness report with index-backed theorem candidates.
4. **render-leantask** — render the L1 Lean skeleton from `leantask_L1.json`.
5. **check-lean** — optional `lake env lean` check through the pinned `lean/` project (skipped when `DEMO_SKIP_LEAN=1` or `lake` is not on `PATH`).
6. **run-readinessbench** — score fixture predictions under `tests/fixtures/readinessbench_predictions/` against ReadinessBench gold (currently one gold item: `finite_tree_edge_count`).
7. **export-public-benchmark / export-public-atlas** — dry-run public JSONL export to a temporary directory (not written to `public_exports/`).

Demo outputs are written under:

```text
artifacts/generated/demo_run/offline/<example_key>/
  alignment.json
  readiness_report.enriched.json
  FiniteTree.lean | CategoryTheoryPullback.lean
```

### Live

Requires `OPENAI_API_KEY`. Before validation, the demo runs model extraction for each example and writes candidate artifacts to:

```text
artifacts/generated/demo_run/live/<example_key>/
  readiness_report.model.json
  proofgraph.model.json
  atlas_record.model.json
  leantask.model.json
```

The remainder of the pipeline uses the committed gold example directories for validate, align, render, and evaluate (model outputs are not promoted into `examples/` or `benchmarks/gold/`).

Public exports in live mode are written to `artifacts/generated/demo_run/live/public_exports/`.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DEMO_SKIP_LEAN` | unset | Set to `1` to skip Lean checking (used in CI and offline Make targets). |
| `OPENAI_API_KEY` | unset | Required for `--live` mode only. |

## Expected output

At the end of a successful run, the demo prints a summary table with:

- example key and `unit_id`
- validation status
- top mathlib alignment candidate
- Lean check status (`passed`, `skipped`, or `failed`)
- output directory path

For offline runs with ReadinessBench fixture predictions, expect a non-null `macro_f1_mean` (currently scored on the `finite_tree_edge_count` gold item).

### finite_tree

- **unit_id:** `finite_tree_edge_count`
- **Top alignment:** `SimpleGraph.IsTree.card_edgeFinset`
- **L1 render:** `FiniteTree.lean` with a `SimpleGraph` tree edge-count skeleton

### category_theory_pullback

- **unit_id:** `category_theory_pullback_equivalence`
- **Top alignment candidates** include pullback-preservation theorems from the category-theory index fixture
- **L1 render:** `CategoryTheoryPullback.lean` with pullback transport skeleton

## What the demo does not do

- Does not overwrite `examples/` or `benchmarks/gold/`.
- Does not call OpenAI in offline mode.
- Does not require network access in offline mode.
- Does not start the review API (`make run-api`); see `apps/review-ui/README.md` for optional UI workflow.

## CI

GitHub Actions runs the offline demo after unit tests:

```yaml
DEMO_SKIP_LEAN=1 python -m fre_core.cli demo --offline --example all
```

## Implementation

Orchestration lives in `packages/fre_core/src/fre_core/demo_runner.py`. The Typer command `demo` in `fre_core.cli` delegates to that module.
