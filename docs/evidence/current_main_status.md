# Current main verification status

Operational proof record for the stabilization sprint. Regenerate after significant changes to `main`:

```bash
make record-main-status
```

| Field | Value |
|-------|-------|
| Commit SHA | `c3542045a433bc46e8f6b8f122416ef306e938aa` |
| Verification date | 2026-06-15 |
| Pytest collection | 352 tests (run `pytest --collect-only -q` on HEAD) |
| `make smoke` / `scripts/dev.ps1 smoke` | pass (local) |
| `verify-release-manifest` | pass |
| `validate-readinessbench` | pass |

## CI runs

| Workflow | Status | Link |
|----------|--------|------|
| `ci.yml` (last run on this SHA) | failure | [Run 27529750721](https://github.com/fraware/formalization-readiness-engine/actions/runs/27529750721) |
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
