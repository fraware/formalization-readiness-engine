# Live baseline notes: finite_tree_edge_count

Local-only scratch notes for live model extraction on the finite-tree reference unit. Do not promote this file to Gold or Silver without review.

## Run metadata

| Field | Value |
|-------|-------|
| Unit ID | `finite_tree_edge_count` |
| Example path | `examples/finite_tree/` |
| Model | _(fill in, e.g. gpt-4.1)_ |
| Schema version | _(fill in from report `schema_version`)_ |
| Run date (UTC) | _(fill in)_ |
| Operator | _(fill in)_ |

## Commands used

```bash
make setup-models
make extract-finite-tree-proofgraph   # optional: proof graph pass
PYTHONPATH=packages/fre_core/src python -m fre_core.cli extract-report \
  examples/finite_tree/unit.json \
  artifacts/generated/finite_tree/readiness_report.model.json
PYTHONPATH=packages/fre_core/src python -m fre_core.cli evaluate-report \
  artifacts/generated/finite_tree/readiness_report.model.json \
  examples/finite_tree/readiness_report.json
make generate-finite-tree-leantask
make render-finite-tree-leantask
make check-lean-finite-tree
```

On Windows without GNU Make:

```powershell
.\scripts\dev.ps1 setup-models
.\scripts\dev.ps1 generate-finite-tree-leantask
.\scripts\dev.ps1 check-lean-finite-tree
```

## Validation outcome

- [ ] Candidate `ReadinessReport` passes Pydantic + semantic validation
- [ ] Evaluation metrics computed without manual reshaping
- [ ] Generated LeanTask renders and typechecks (L1 `sorry` scaffold policy)

## Dimension-level observations

### Existing theorem candidates

_(List false positives, missed mathlib names, namespace issues.)_

### Constructive path

_(Note missing steps, wrong ordering, or over-specific lemmas.)_

### Blockers

_(Note hallucinated blockers or missed real gaps.)_

### Proof graph / Atlas (if run)

_(Optional: edge errors, atlas evidence gaps.)_

### LeanTask / formal target

_(Optional: import gaps, binder mismatches, alignment target notes.)_

## Error summary

| Category | Count | Examples |
|----------|-------|----------|
| Notation / parsing | | |
| Wrong existing-theorem candidate | | |
| Constructive path gap | | |
| Blocker false positive | | |
| Lean scaffold mismatch | | |

## Follow-ups

1. _(Action items for review or benchmark promotion.)_
