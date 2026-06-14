# Reviewer Guide

This guide explains how to review one theorem/proof unit and its readiness report without reading the codebase. It supports the Bronze to Silver to Gold promotion path used by ReadinessBench.

## What you are reviewing

Each review unit consists of:

1. A **theorem/proof unit** (`unit.json`): the informal statement, optional proof, source link, and domain metadata.
2. A **readiness report** (`readiness_report.json`): a structured assessment of formalization readiness across four dimensions, plus candidate theorem names, a constructive path, blockers, and a recommended next action.

Your job is to decide whether the readiness report is accurate, useful to an external formalizer, and ready for promotion to Silver or Gold.

## v0.2 gold disclaimer

The 11 gold fixtures in `benchmarks/readinessbench/gold/` are labeled `review_origin: internal_seed`. They were seeded by the engineering team for benchmark scale and reproducibility. They are **not** community-validated external truth despite carrying `review_status: expert_reviewed`.

To promote an item to `review_origin: external_expert`, complete this review workflow, persist the submission under `benchmarks/readinessbench/edits/`, and reference that path (not the template placeholder) in `gold/changelog.jsonl`.

## Before you start

Collect these files for the unit under review:

| File | Purpose |
|------|---------|
| `unit.json` | Source statement and proof text |
| `readiness_report.json` | Candidate or prior-tier report to evaluate |
| Optional prior tier report | Compare Bronze against Silver corrections |

Use the finite-tree reference unit as a worked example:

- Unit: `examples/finite_tree/unit.json`
- Candidate report: `examples/finite_tree/readiness_report.json` or `benchmarks/readinessbench/bronze/finite_tree_edge_count/readiness_report.json`
- Silver fixture: `benchmarks/readinessbench/silver/finite_tree_edge_count/readiness_report.json`
- Gold fixture: `benchmarks/readinessbench/gold/finite_tree_edge_count/readiness_report.json`

You do not need Python, Lean, or repository checkout beyond these JSON files.

## Review workflow

### Step 1: Read the source unit

1. Read `statement` and `proof` in `unit.json`.
2. Confirm `unit_id` matches the report under review.
3. Note domain-specific terminology (for example, tree, leaf, deletion notation).

### Step 2: Evaluate readiness dimensions

For each dimension in the readiness report, check accuracy against the source unit:

| Report field | Question |
|--------------|----------|
| `statement_readiness` | Is the theorem statement correctly classified and decomposed? |
| `context_readiness` | Are assumptions and missing context identified? |
| `notation_readiness` | Are symbols and informal notation gaps listed? |
| `dependency_readiness` | Are proof dependencies and missing lemmas identified? |

Each dimension has:

- `status`: coarse readiness label (`clear`, `partial`, or project-specific values)
- `recovered`: elements correctly extracted from the source
- `unresolved`: gaps that still block formalization
- `notes`: free-text reviewer-facing explanation

Record your assessment in `docs/review/READINESS_REPORT_REVIEW_FORM.md` or directly in the JSON submission template.

### Step 3: Evaluate list fields and next action

Check these top-level report fields:

| Field | Review criterion |
|-------|------------------|
| `existing_theorem_candidates` | Names must be justified by source text, mathlib knowledge, or index lookup evidence. Do not accept invented declaration names. |
| `constructive_path` | Steps must follow from the informal proof strategy. |
| `blockers` | Each blocker must name a concrete alignment or infrastructure gap. |
| `recommended_next_action` | Must be actionable for the next pipeline stage. |

### Step 4: Score external usefulness

Apply `docs/review/USEFULNESS_RUBRIC.md`. Score each rubric dimension from 1 (poor) to 5 (excellent).

Silver promotion generally requires no dimension below 3. Gold promotion generally requires no dimension below 4 and expert confirmation of library alignment.

### Step 5: Decide tier promotion

| Target tier | Required `review_status` | Minimum bar |
|-------------|--------------------------|-------------|
| Silver | `human_reviewed` | Obvious extraction errors corrected; source spans checked where available; list fields grounded in the unit |
| Gold | `expert_reviewed` | Mathematical correctness of readiness assessment; library candidates verified; blockers and next action stable for benchmark use |

If the report is not promotable, set `review_status` to `rejected` or `deferred` and explain why in `notes`. Do not copy the report into Silver or Gold directories.

### Step 6: Produce structured review output

1. Copy `docs/review/templates/readiness_report_review.json` to a review output path (for example `reviews/finite_tree_edge_count/review.json`).
2. Fill all required fields.
3. Either attach a corrected report inline (`corrected_report`) or reference its path (`corrected_report_path`).
4. Validate the submission:

```bash
PYTHONPATH=packages/fre_core/src python -m fre_core.cli validate-review-submission reviews/finite_tree_edge_count/review.json
```

On Windows:

```powershell
$env:PYTHONPATH = "packages/fre_core/src"
python -m fre_core.cli validate-review-submission reviews/finite_tree_edge_count/review.json
```

### Step 7: Promote artifacts to ReadinessBench

After review approval:

1. Write the corrected readiness report with the appropriate `review_status`.
2. Copy reviewed artifacts into `benchmarks/readinessbench/silver/<unit_id>/` or `benchmarks/readinessbench/gold/<unit_id>/`.
3. Update `benchmarks/readinessbench/manifest.json` if the item is new.
4. For Gold changes, append an entry to `benchmarks/readinessbench/gold/changelog.jsonl` and `benchmarks/readinessbench/gold/CHANGELOG.md`, including `review_origin` (`external_expert` when this guide's workflow produced the submission).

Never promote directly from `artifacts/generated/` without completing this review workflow.

## Quality rules

- Prefer evidence over speculation. If a theorem candidate cannot be justified, remove it or mark the report as not promotable.
- Preserve `unit_id` across all artifacts in a review unit.
- Do not change the mathematical statement in the unit unless the source itself is wrong and that correction is documented separately.
- When two reviewers disagree, record uncertainty in dimension `notes` and defer Gold promotion until resolved.

## Related documents

- `READINESS_REPORT_REVIEW_FORM.md` — field-by-field review template
- `USEFULNESS_RUBRIC.md` — scoring criteria
- `EDIT_EXAMPLES.md` — acceptable and unacceptable edits
- `benchmarks/readinessbench/README.md` — tier layout and evaluation rules
