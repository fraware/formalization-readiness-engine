# Current main verification status

Operational proof record for the stabilization sprint. Regenerate after significant changes to `main`.

| Field | Value |
|-------|-------|
| Commit SHA | `f411fd5f1a6b6e4a5624970a26d1c33614b17f0b` |
| Verification date | 2026-06-14 |
| Pytest collection | 340 tests (run `pytest --collect-only -q` on HEAD) |
| `make smoke` / `.\scripts\dev.ps1 smoke` | pass (local) |
| `verify-release-manifest` | pass |
| `validate-readinessbench` | pass |

## CI runs

| Workflow | Status | Link |
|----------|--------|------|
| `ci.yml` (last run on this SHA) | success | [Run 27514905898](https://github.com/fraware/formalization-readiness-engine/actions/runs/27514905898) |
| `lean.yml` (manual dispatch) | success | [Run 27514933703](https://github.com/fraware/formalization-readiness-engine/actions/runs/27514933703) |

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
