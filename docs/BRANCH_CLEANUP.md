# Branch Cleanup

The initial engineering sprint used short-lived branches for focused PRs. All accepted work was squash-merged into `main`.

## Branches that can be removed

After confirming `main` is current, the following branches can be removed from GitHub:

- `engineering-core-validation`
- `engineering-schema-export`
- `engineering-latex-ingestion`
- `engineering-leantask-renderer`
- `engineering-corpus-catalog`
- `engineering-lean-check-runner`
- `engineering-readinessbench-metrics`

The connected tool interface used during this handoff pass did not expose branch deletion. Remove these branches through the GitHub UI or with a local Git client.

## UI cleanup

1. Open the repository on GitHub.
2. Go to the branches view.
3. Confirm each branch above has a merged pull request.
4. Remove each merged engineering branch.
5. Keep only `main` and any new active engineering branch.

## Future rule

Use one branch per PR. Remove branches after merge unless the branch is a long-running release branch. Avoid leaving merged engineering branches in the repository because they make takeover status harder to read.
