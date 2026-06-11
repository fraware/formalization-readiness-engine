# Edit Examples: Acceptable and Unacceptable Changes

These examples show how to promote candidate readiness reports to Silver or Gold. They apply to the finite-tree unit (`finite_tree_edge_count`) but generalize to any unit.

## Acceptable edits

### Correct a dimension status and notes (Silver)

**Before (candidate):**

```json
"context_readiness": {
  "status": "clear",
  "recovered": ["graph"],
  "unresolved": [],
  "notes": null
}
```

**After (Silver):**

```json
"context_readiness": {
  "status": "partial",
  "recovered": ["graph", "vertex set", "edge set", "finiteness", "tree assumption"],
  "unresolved": ["target library definition of leaf", "target representation of graph deletion"],
  "notes": "Tree and leaf terminology must be aligned with mathlib definitions."
}
```

**Why acceptable:** The reviewer grounded recovered items in the source unit and listed real alignment gaps.

### Replace free-text theorem guess with index-backed candidate (Silver)

**Before:**

```json
"existing_theorem_candidates": ["Tree.card_edges_lemma"]
```

**After:**

```json
"existing_theorem_candidates": ["SimpleGraph.IsTree.card_edgeFinset"]
```

**Why acceptable:** The candidate name comes from a reproducible mathlib index lookup or expert verification, not model invention.

### Refine blockers without changing mathematical content (Silver to Gold)

**Before:**

```json
"blockers": ["formalization hard", "needs mathlib"]
```

**After:**

```json
"blockers": [
  "definition alignment for finite tree",
  "definition alignment for leaf",
  "formal representation of G-v",
  "decision between existing-theorem reuse and constructive decomposition"
]
```

**Why acceptable:** Blockers become specific infrastructure decisions while preserving the underlying mathematical task.

### Set review status on promotion (Silver or Gold)

**Silver:**

```json
"review_status": "human_reviewed"
```

**Gold:**

```json
"review_status": "expert_reviewed"
```

**Why acceptable:** Tier promotion requires explicit review status aligned with ReadinessBench tier rules.

### Document Gold changes in the changelog

When any Gold field changes, append matching entries to:

- `benchmarks/readinessbench/gold/changelog.jsonl`
- `benchmarks/readinessbench/gold/CHANGELOG.md`

**Why acceptable:** Gold is evaluated benchmark truth; changes must be auditable.

## Unacceptable edits

### Invent theorem names without evidence

**Unacceptable:**

```json
"existing_theorem_candidates": ["GraphTheory.FiniteTree.edge_cardinality_theorem"]
```

**Why unacceptable:** The name is not verified in mathlib or the declaration index. Remove the entry or replace it with an evidenced candidate.

### Alter the mathematical statement in the unit without source justification

**Unacceptable:** Changing `unit.json` statement from `|E| = |V| - 1` to a different formula to match a wrong report.

**Why unacceptable:** Unit text must track the source document. Fix the report, not the theorem, unless the catalog source itself is corrected through a separate source-review process.

### Copy generated output directly into Gold

**Unacceptable:** Copying `artifacts/generated/finite_tree/readiness_report.model.json` into `benchmarks/readinessbench/gold/` without review fields, rubric scores, and changelog entry.

**Why unacceptable:** Generated artifacts are Bronze candidates only. Gold requires expert review and audit trail.

### Silent Gold edits

**Unacceptable:** Editing `benchmarks/readinessbench/gold/finite_tree_edge_count/readiness_report.json` without updating `gold/changelog.jsonl` and `gold/CHANGELOG.md`.

**Why unacceptable:** Benchmark truth must remain auditable for external users and inter-annotator checks.

### Weakening blockers to pass validation

**Unacceptable:** Deleting all blockers while `recommended_next_action` still references unresolved alignment work.

**Why unacceptable:** Semantic validation requires at least one formalization path; empty blockers with a constructive path must still be internally consistent.

### Promote with wrong review status

**Unacceptable:** Gold manifest item with `"review_status": "candidate"` or Silver item with `"review_status": "expert_reviewed"` without tier justification.

**Why unacceptable:** ReadinessBench manifest validation rejects tier and status mismatches.

## Quick decision table

| Change | Acceptable when |
|--------|-----------------|
| Fix dimension `status` | Supported by source text |
| Add/remove list items | Each item traceable to source or mathlib evidence |
| Rewrite `notes` | Clarifies reviewer reasoning |
| Change `review_status` | Matches Silver or Gold promotion decision |
| Edit Gold fixture | Changelog updated; review submission archived |
| Edit unit statement | Only when catalog source is corrected and documented |
