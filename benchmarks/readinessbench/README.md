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

Tier paths must live under the matching tier prefix (`gold/`, `silver/`, or `bronze/`). Paths under `artifacts/generated/` are rejected.

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

The runner writes a deterministic JSON report with per-item and mean macro-F1 scores.

## Promoting artifacts

1. Write model output under `artifacts/generated/` with `review_status: candidate`.
2. Follow the external review workflow in `docs/review/REVIEWER_GUIDE.md`.
3. Review and correct fields using `docs/review/READINESS_REPORT_REVIEW_FORM.md` and score with `docs/review/USEFULNESS_RUBRIC.md`.
4. Submit structured review JSON (template: `docs/review/templates/readiness_report_review.json`) and run `validate-review-submission`.
5. Copy reviewed artifacts into the appropriate tier directory and add or update `manifest.json`.
6. For Gold changes, append entries to `gold/changelog.jsonl` and `gold/CHANGELOG.md`, then run `validate-gold-changelog`.
7. Never copy directly from `artifacts/generated/` into Gold without an explicit review step.

See also `docs/review/EDIT_EXAMPLES.md` for acceptable and unacceptable edits.
