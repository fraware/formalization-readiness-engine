# Branch Cleanup

The initial engineering sprint used short-lived branches for focused PRs. All accepted work was squash-merged into `main`.

## Branches that can be removed (first handoff, merged into original `main`)

After confirming `main` is current, the following branches can be removed from GitHub:

- `engineering-core-validation`
- `engineering-schema-export`
- `engineering-latex-ingestion`
- `engineering-leantask-renderer`
- `engineering-corpus-catalog`
- `engineering-lean-check-runner`
- `engineering-readinessbench-metrics`

## Branches to remove after Wave 0 merges to `main`

Once `engineering/wave0-hygiene` (or equivalent consolidation PR) is merged, delete the stacked sprint and demo branches if they are fully contained in `main`:

- `engineering-sprint1-readiness-harness` through `engineering-sprint7-review-workflow`
- `engineering-category-theory-example`
- `engineering-leantask-generation`
- `engineering-phase5-6-north-star`
- `engineering-e2e-demo-integration`

See `docs/ENGINEERING_BRANCH_STATUS.md` for the ahead/behind matrix before deletion.

Remove branches through the GitHub UI or with a local Git client.

## UI cleanup

1. Open the repository on GitHub.
2. Go to the branches view.
3. Confirm each branch above has a merged pull request.
4. Remove each merged engineering branch.
5. Keep only `main` and any new active engineering branch.

## Future rule

Use one branch per PR. Remove branches after merge unless the branch is a long-running release branch. Avoid leaving merged engineering branches in the repository because they make takeover status harder to read.
