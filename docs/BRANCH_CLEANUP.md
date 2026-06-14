# Branch cleanup

Completed June 2026. This document records the removal of temporary engineering branches after the public release merge to `main`.

## Outcome

All accepted engineering work was squash-merged into `main`. The following branch families were deleted from the remote after verification:

- First-handoff branches: `engineering-core-validation`, `engineering-schema-export`, `engineering-latex-ingestion`, `engineering-leantask-renderer`, `engineering-corpus-catalog`, `engineering-lean-check-runner`, `engineering-readinessbench-metrics`
- Sprint stack: `engineering-sprint1-readiness-harness` through `engineering-sprint7-review-workflow`
- Feature branches: `engineering-category-theory-example`, `engineering-leantask-generation`, `engineering-phase5-6-north-star`, `engineering-e2e-demo-integration`
- Hygiene branch: `engineering/wave0-hygiene`

Only `main` and new feature branches should remain active.

## Verification before deletion

1. Confirm `main` passes CI (`make check`, docs build, offline demo).
2. Confirm required files exist on `main` (Lean pins, corpus catalog, ReadinessBench manifest, public exports).
3. Remove merged branches through the GitHub UI or a local Git client.

## Future rule

Use one branch per pull request. Delete branches after merge unless the branch is a long-running release branch. Avoid leaving merged engineering branches in the repository because they obscure release status for new contributors.
