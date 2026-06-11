# Readiness Report Review Form

Use this form when reviewing one theorem/proof unit. Fields map directly to the `ReadinessReport` schema and to the JSON review submission template at `docs/review/templates/readiness_report_review.json`.

## Review metadata

| Field | Value |
|-------|-------|
| Unit ID | |
| Benchmark item ID (if applicable) | |
| Reviewer ID | |
| Review date (YYYY-MM-DD) | |
| Source unit path | |
| Report under review path | |
| Target tier promotion | `silver` / `gold` / none |
| Final `review_status` | `human_reviewed` / `expert_reviewed` / `rejected` / `deferred` |

## Dimension review

For each dimension, mark whether the report content is accurate against the source unit. Use `notes` for corrections you would make.

### Statement readiness (`statement_readiness`)

| Check | Pass | Fail | Notes |
|-------|------|------|-------|
| `status` is appropriate | | | |
| `recovered` items match the source statement | | | |
| `unresolved` items are genuine gaps (or correctly empty) | | | |

### Context readiness (`context_readiness`)

| Check | Pass | Fail | Notes |
|-------|------|------|-------|
| `status` is appropriate | | | |
| `recovered` context matches the unit | | | |
| `unresolved` context gaps are real | | | |

### Notation readiness (`notation_readiness`)

| Check | Pass | Fail | Notes |
|-------|------|------|-------|
| `status` is appropriate | | | |
| `recovered` notation is complete | | | |
| `unresolved` notation gaps are identified | | | |

### Dependency readiness (`dependency_readiness`)

| Check | Pass | Fail | Notes |
|-------|------|------|-------|
| `status` is appropriate | | | |
| `recovered` dependencies match the proof strategy | | | |
| `unresolved` dependencies are proof-relevant | | | |

## List fields and next action

| Field | Accurate (yes/no) | Required edits |
|-------|-------------------|----------------|
| `existing_theorem_candidates` | | |
| `constructive_path` | | |
| `blockers` | | |
| `recommended_next_action` | | |

Set `list_fields_accurate` to `true` only if all four list/action fields need no correction.

## External usefulness rubric

Score each dimension 1–5 using `USEFULNESS_RUBRIC.md`.

| Rubric dimension | Score (1–5) | Notes |
|------------------|-------------|-------|
| Source fidelity | | |
| Actionability | | |
| Library alignment | | |
| Blocker specificity | | |
| Path clarity | | |

## Corrected report

| Option | Path or inline |
|--------|----------------|
| No corrections needed | Set `list_fields_accurate: true` and leave corrected fields empty |
| Corrected report file | `corrected_report_path` |
| Inline corrected report | `corrected_report` object in submission JSON |

Corrected reports must keep the same `unit_id` and set `review_status` to the final promoted status.

## Promotion decision

| Decision | Condition |
|----------|-----------|
| Promote to Silver | Human review complete; rubric scores acceptable; corrections applied or confirmed |
| Promote to Gold | Expert review complete; library candidates verified; stable for benchmark scoring |
| Reject | Report is misleading or not recoverable without re-extraction |
| Defer | Insufficient evidence or unresolved reviewer disagreement |

## Reviewer notes

Summarize changes, open questions, and evidence used (source spans, mathlib declaration names, prior tier diffs):

```
Notes:

```

## Submission checklist

- [ ] All dimension review flags recorded in submission JSON
- [ ] Rubric scores filled
- [ ] `review_status` matches target tier
- [ ] Corrected report provided when list fields were inaccurate
- [ ] `validate-review-submission` passes on the submission file
- [ ] Gold changes logged in `benchmarks/readinessbench/gold/CHANGELOG.md` and `changelog.jsonl`
