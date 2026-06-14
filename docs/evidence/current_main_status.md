# Current main verification status

Operational proof record for the stabilization sprint. Regenerate after significant changes to `main`.

| Field | Value |
|-------|-------|
| Commit SHA | `20a7200f26498973c8988b9e146909f73125cac9` |
| Verification date | 2026-06-14 |
| Pytest collection | 339 tests (run `pytest --collect-only -q` on HEAD) |
| `make smoke` / `.\scripts\dev.ps1 smoke` | pass (local) |
| `verify-release-manifest` | pass |
| `validate-readinessbench` | pass |

## CI runs

| Workflow | Status | Link |
|----------|--------|------|
| `ci.yml` (last run on this SHA) | failed — release manifest checksum mismatch on committed `atlas.jsonl`; local working tree passes `verify-release-manifest` | [Run 27512081855](https://github.com/fraware/formalization-readiness-engine/actions/runs/27512081855) |
| `lean.yml` (manual dispatch) | success | [Run 27514195954](https://github.com/fraware/formalization-readiness-engine/actions/runs/27514195954) |

Lean CI does not run on every push. It is path-filtered to generated Lean tasks, the pinned toolchain, and `leantask*.py`. Trigger manually when those paths are unchanged:

```bash
gh workflow run lean.yml
```

List recent runs:

```bash
gh run list --workflow=lean.yml --limit 5
```

## Local smoke checklist

```bash
make smoke
```

Windows:

```powershell
.\scripts\dev.ps1 smoke
```

Equivalent steps: `setup`, `test`, `validate-examples`, `validate-readinessbench`, `verify-release-manifest`, `docs`.
