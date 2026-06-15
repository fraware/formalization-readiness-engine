# ReadinessBench

ReadinessBench is the artifact-first benchmark for readiness-report extraction. Items are organized into explicit Bronze, Silver, and Gold tiers. Generated model output never enters this tree without review, and evaluation always scores predictions against Gold items only.

## Manifest scale (v0.2.0)

The committed manifest (`manifest.json`) lists 43 items:

| Tier | Count | Scored in evaluation? |
|------|-------|----------------------|
| gold | 11 | Yes |
| silver | 1 | No (promotion example) |
| bronze | 31 | No (corpus-scale candidates) |

## Tier definitions

| Tier | `review_status` allowed | Purpose |
|------|-------------------------|---------|
| bronze | `candidate`, `machine_validated` | Automatically extracted reports; schema-valid and source-linked but not guaranteed correct |
| silver | `human_reviewed` | Reviewer-corrected reports with checked spans and fixed obvious errors |
| gold | `human_reviewed`, `expert_reviewed` | Expert-reviewed benchmark truth used for scoring |

## Gold provenance (v0.2)

All 11 v0.2 gold items carry `review_origin: internal_seed`. They are **engineering-curated fixtures** seeded for benchmark scale, not community-validated external truth. The `review_status: expert_reviewed` label reflects internal curation quality targets, not independent expert sign-off.

Reserve `review_origin: external_expert` or `community_reviewed` for items promoted through the external review workflow with persisted submissions under `benchmarks/readinessbench/edits/`. Public JSONL exports include `review_origin` on each record.

## v0.2 lexical baseline metrics

ReadinessBench scoring uses **normalized set-overlap F1** (lexical token matching) for:

- `existing_theorem_candidates`
- `constructive_path`
- `blockers`
- `notation_readiness.recovered` / `unresolved`

This measures string overlap, not semantic equivalence. A prediction can cite a mathematically relevant mathlib declaration and still score 0.0 when the gold string differs lexically (for example `CategoryTheory` vs `category_theory`). Optional ProofGraph, Atlas, and LeanTask scores use the same lexical overlap approach.

Semantic or embedding-based metrics are planned for v0.3; see `docs/NEXT_SPRINTS.md`.

## v0.3 semantic metrics (declaration-ID and ontology)

The v0.3 evaluation layer (`fre_core.evaluation_v03`) runs **in parallel** with lexical v0.2 scoring:

| Column | Meaning |
|--------|---------|
| `macro_f1_mean` | v0.2 lexical overlap (unchanged baseline) |
| `v03_macro_f1_mean` | Aggregate semantic score across scored items |
| `v03_metrics.theorem_candidates_declaration_f1` | Theorem candidates resolved via mathlib index `full_name` / `declaration_id`, with optional alias groups under `equivalence/<unit_id>.json` |
| `v03_metrics.blockers_ontology_f1` | Blockers mapped to Atlas `blocker_type` vocabulary before set F1 |
| `v03_metrics.proofgraph_node_type_f1` | ProofGraph node types after public-export normalization |
| `v03_metrics.atlas_blocker_type_f1` | Atlas `blocker_type` after controlled-vocabulary normalization |

CLI output from `run-readinessbench` and `run-benchmark-evaluation` prints both lexical and v0.3 means when available. Live extraction evidence under `docs/evidence/live_extraction_v0.2/` records both score families in `summary.json`.

Lexical F1 remains the regression baseline; v0.3 scores reflect semantic relevance where string overlap is zero (for example category-theory theorem aliases).

## Layout

```text
benchmarks/readinessbench/
  README.md
  manifest.json
  gold/<unit_id>/
    unit.json
    readiness_report.json
  silver/<unit_id>/          # optional corrected fixtures
  bronze/<unit_id>/          # optional candidate fixtures
```

Each manifest item declares:

- `item_id`: stable benchmark identifier
- `unit_id`: theorem/proof unit identifier shared across artifacts
- `tier`: `bronze`, `silver`, or `gold`
- `unit_path` and `readiness_report_path`: paths relative to this directory

Tier paths must live under the matching tier prefix (`gold/`, `silver/`, or `bronze/`). Manifest and gold truth paths under `artifacts/generated/` are rejected. Prediction inputs may live under `artifacts/generated/` (for example after `make demo-live`).

## Gold is evaluated truth

Only Gold items participate in benchmark scoring. Silver and Bronze items document the promotion path from extraction to reviewed truth. A report with `review_status: candidate` cannot be listed as Gold in the manifest; validation fails before scoring runs.

The hand-authored reference stacks remain at `examples/finite_tree/` and `examples/category_theory_pullback/`. Gold benchmark copies are the evaluated truth set and may diverge after expert review.

The category-theory example is **examples-only** until it passes external review. It is not listed in `manifest.json` and does not participate in benchmark scoring yet.

## Running evaluation

Provide predicted readiness reports in a directory keyed by `unit_id`:

```text
predictions/
  finite_tree_edge_count/
    readiness_report.json
```

Live extraction output under `artifacts/generated/` is valid for scoring. Demo live runs write example-key folders with model artifacts:

```text
artifacts/generated/demo_run/live/
  finite_tree/
    readiness_report.model.json
  category_theory_pullback/
    readiness_report.model.json
```

Point `PREDICTIONS_DIR` at the parent directory (for example `artifacts/generated/demo_run/live`). The scorer resolves predictions by `unit_id` inside each JSON file, so example-key folder names do not need to match gold `unit_id` values.

Standard benchmark layout (also supported):

```text
predictions/
  finite_tree_edge_count/
    readiness_report.json
```

Commands:

```bash
make validate-readinessbench
make run-readinessbench PREDICTIONS_DIR=tests/fixtures/readinessbench_predictions
```

On Windows:

```powershell
.\scripts\dev.ps1 validate-readinessbench
.\scripts\dev.ps1 run-readinessbench -PredictionsDir tests/fixtures/readinessbench_predictions
```

The runner writes a deterministic JSON report with per-item and mean macro-F1 scores. Gold items without a matching prediction are skipped; at least one scored item is required.

## Promoting artifacts

1. Write model output under `artifacts/generated/` with `review_status: candidate`.
2. Follow the external review workflow in `docs/review/REVIEWER_GUIDE.md`.
3. Review and correct fields using `docs/review/READINESS_REPORT_REVIEW_FORM.md` and score with `docs/review/USEFULNESS_RUBRIC.md`.
4. Submit structured review JSON (template: `docs/review/templates/readiness_report_review.json`) and run `validate-review-submission`.
5. Copy reviewed artifacts into the appropriate tier directory and add or update `manifest.json`.
6. For Gold changes, append entries to `gold/changelog.jsonl` and `gold/CHANGELOG.md`, then run `validate-gold-changelog`.
7. Never copy directly from `artifacts/generated/` into Gold without an explicit review step.

See also `docs/review/EDIT_EXAMPLES.md` for acceptable and unacceptable edits.
