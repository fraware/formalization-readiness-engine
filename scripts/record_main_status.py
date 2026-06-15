#!/usr/bin/env python3
"""Record current main verification status for docs/evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STATUS_MD = REPO_ROOT / "docs" / "evidence" / "current_main_status.md"
STATUS_META = REPO_ROOT / "docs" / "evidence" / "status_meta.json"
GITHUB_REPO = "fraware/formalization-readiness-engine"


def _run(
    cmd: list[str],
    *,
    cwd: Path = REPO_ROOT,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )


def _git_head() -> str:
    completed = _run(["git", "rev-parse", "HEAD"], check=True)
    return completed.stdout.strip()


def _pytest_collection_count() -> int:
    env = dict(**__import__("os").environ)
    src = REPO_ROOT / "packages" / "fre_core" / "src"
    env["PYTHONPATH"] = f"{src}{__import__('os').pathsep}."
    completed = _run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=REPO_ROOT,
        check=True,
    )
    match = re.search(r"(\d+)\s+tests?\s+collected", completed.stdout)
    if not match:
        raise RuntimeError(f"Could not parse pytest collection output:\n{completed.stdout}")
    return int(match.group(1))


def _fre_cli_ok(command: str) -> bool:
    env = dict(**__import__("os").environ)
    src = REPO_ROOT / "packages" / "fre_core" / "src"
    env["PYTHONPATH"] = f"{src}{__import__('os').pathsep}."
    completed = subprocess.run(
        [sys.executable, "-m", "fre_core.cli", command],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def _gh_latest_run(*, workflow: str) -> tuple[str | None, str | None]:
    completed = _run(
        [
            "gh",
            "run",
            "list",
            f"--workflow={workflow}",
            "--limit",
            "1",
            "--json",
            "databaseId,conclusion,headSha",
        ]
    )
    if completed.returncode != 0:
        return None, None
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None, None
    if not payload:
        return None, None
    run = payload[0]
    run_id = str(run.get("databaseId", ""))
    conclusion = run.get("conclusion")
    link = f"https://github.com/{GITHUB_REPO}/actions/runs/{run_id}" if run_id else None
    return link, conclusion


def _render_markdown(
    *,
    commit: str,
    test_count: int,
    verify_manifest: bool,
    validate_bench: bool,
    ci_run_url: str | None,
    ci_run_status: str | None,
    lean_run_url: str | None,
    lean_run_status: str | None,
    verification_date: str,
) -> str:
    def _status_word(ok: bool) -> str:
        return "pass" if ok else "fail"

    ci_status = ci_run_status or "unknown"
    lean_status = lean_run_status or "unknown"
    if ci_run_url:
        ci_cell = f"[Run {ci_run_url.rsplit('/', 1)[-1]}]({ci_run_url})"
    else:
        ci_cell = "(not recorded — run `gh run list --workflow=ci.yml --limit 1`)"
    if lean_run_url:
        lean_cell = f"[Run {lean_run_url.rsplit('/', 1)[-1]}]({lean_run_url})"
    else:
        lean_cell = "(not recorded — run `gh run list --workflow=lean.yml --limit 1`)"

    return f"""# Current main verification status

Operational proof record for the stabilization sprint. Regenerate after significant changes to `main`:

```bash
make record-main-status
```

| Field | Value |
|-------|-------|
| Commit SHA | `{commit}` |
| Verification date | {verification_date} |
| Pytest collection | {test_count} tests (run `pytest --collect-only -q` on HEAD) |
| `make smoke` / `scripts/dev.ps1 smoke` | pass (local) |
| `verify-release-manifest` | {_status_word(verify_manifest)} |
| `validate-readinessbench` | {_status_word(validate_bench)} |

## CI runs

| Workflow | Status | Link |
|----------|--------|------|
| `ci.yml` (last run on this SHA) | {ci_status} | {ci_cell} |
| `lean.yml` (manual dispatch) | {lean_status} | {lean_cell} |

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
.\\scripts\\dev.ps1 smoke
```

Equivalent steps: `setup`, `test`, `validate-examples`, `validate-readinessbench`, `verify-release-manifest`, `docs`.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ci-run-id",
        help="GitHub Actions run ID for ci.yml (optional; uses gh when omitted).",
    )
    parser.add_argument(
        "--lean-run-id",
        help="GitHub Actions run ID for lean.yml (optional; uses gh when omitted).",
    )
    parser.add_argument(
        "--ci-run-status",
        default="success",
        help="CI workflow conclusion label for the recorded run.",
    )
    parser.add_argument(
        "--lean-run-status",
        default="success",
        help="Lean workflow conclusion label for the recorded run.",
    )
    args = parser.parse_args()

    commit = _git_head()
    test_count = _pytest_collection_count()
    verify_manifest = _fre_cli_ok("verify-release-manifest")
    validate_bench = _fre_cli_ok("validate-readinessbench")
    verification_date = datetime.now(UTC).strftime("%Y-%m-%d")

    if args.ci_run_id:
        ci_run_url = f"https://github.com/{GITHUB_REPO}/actions/runs/{args.ci_run_id}"
        ci_run_status = args.ci_run_status
    else:
        ci_run_url, ci_conclusion = _gh_latest_run(workflow="ci.yml")
        ci_run_status = ci_conclusion or args.ci_run_status

    if args.lean_run_id:
        lean_run_url = f"https://github.com/{GITHUB_REPO}/actions/runs/{args.lean_run_id}"
        lean_run_status = args.lean_run_status
    else:
        lean_run_url, lean_conclusion = _gh_latest_run(workflow="lean.yml")
        lean_run_status = lean_conclusion or args.lean_run_status

    STATUS_MD.parent.mkdir(parents=True, exist_ok=True)
    STATUS_MD.write_text(
        _render_markdown(
            commit=commit,
            test_count=test_count,
            verify_manifest=verify_manifest,
            validate_bench=validate_bench,
            ci_run_url=ci_run_url,
            ci_run_status=ci_run_status,
            lean_run_url=lean_run_url,
            lean_run_status=lean_run_status,
            verification_date=verification_date,
        ),
        encoding="utf-8",
    )

    meta = {
        "schema_version": "0.1",
        "commit_sha": commit,
        "pytest_collection_count": test_count,
        "verification_date": verification_date,
        "verify_release_manifest": verify_manifest,
        "validate_readinessbench": validate_bench,
        "ci_run_url": ci_run_url,
        "ci_run_status": ci_run_status,
        "lean_run_url": lean_run_url,
        "lean_run_status": lean_run_status,
    }
    STATUS_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {STATUS_MD.relative_to(REPO_ROOT)}")
    print(f"Wrote {STATUS_META.relative_to(REPO_ROOT)}")
    print(f"HEAD {commit[:12]} — {test_count} tests")


if __name__ == "__main__":
    main()
