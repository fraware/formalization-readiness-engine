# Engineering branch merge status

Snapshot for Wave 0 hygiene (2026-06-14). Use this before deleting branches or starting scale-up work.

## Base branch

`main` is at `a44b4f1` (initial handoff: schemas, finite-tree example, first engineering docs). It does **not** yet include Sprints 1–7, category theory, LeanTask generation, Phase 5–6, or E2E demo work.

## Unmerged engineering branches (ahead of `main`)

All branches below are **0 commits behind** `main` unless noted. They form a linear stack ending at `engineering-e2e-demo-integration`.

| Branch | Commits ahead of `main` | Summary |
|--------|-------------------------|---------|
| `engineering-sprint1-readiness-harness` | 1 (also 1 behind) | Readiness harness + handoff docs; diverged from later sprint history |
| `engineering-sprint2-pinned-lean` | 2 (also 2 behind) | Lean v4.8.0 + mathlib pin, `lake-manifest.json`, Generated finite-tree scaffold |
| `engineering-sprint3-corpus-catalog` | 1 | Corpus catalog ingestion and shareable export |
| `engineering-sprint4-graph-atlas-extraction` | 2 | ProofGraph and Atlas extraction |
| `engineering-sprint5-mathlib-index` | 3 | Mathlib declaration index v0 |
| `engineering-sprint6-readinessbench-tiers` | 4 | ReadinessBench tier layout and evaluation runner |
| `engineering-sprint7-review-workflow` | 5 | External review workflow |
| `engineering-category-theory-example` | 6 | Category-theory pullback reference example |
| `engineering-leantask-generation` | 7 | LeanTask generation from readiness reports |
| `engineering-phase5-6-north-star` | 10 | Alignment service, review API/UI, public export |
| `engineering-e2e-demo-integration` | 11 | End-to-end offline demo for both reference examples |

**Recommended consolidation tip:** merge or squash-merge `engineering-e2e-demo-integration` into `main`, then re-apply Sprint 2 Lean pin files if absent (`lean-toolchain`, `lake-manifest.json`, `lean/README.md`, `lean/FRETasks/Generated/`).

## Wave 0 hygiene branch

`engineering/wave0-hygiene` extends `engineering-e2e-demo-integration` with:

- Sprint 2 Lean pin essentials restored on the consolidated tip
- Live baseline `artifacts/generated/finite_tree/NOTES.md` template
- Updated handoff and branch documentation
- Lean pin smoke tests

## Branches already documented for deletion (merged into original handoff `main`)

See `docs/BRANCH_CLEANUP.md` for the first-sprint branches (`engineering-core-validation`, etc.).

## After Wave 0 merges to `main`

1. Delete merged `engineering-sprint*` and `engineering-e2e-demo-integration` branches per `docs/BRANCH_CLEANUP.md`.
2. Rebase active wave branches (`engineering/wave1-*`, etc.) onto updated `main`.
