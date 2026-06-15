"""Optional guards for committed documentation evidence."""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "evidence" / "live_extraction_v0.2"
LIVE_EXTRACTION_SUMMARY = EVIDENCE_DIR / "summary.json"
CURRENT_MAIN_STATUS = ROOT / "docs" / "evidence" / "current_main_status.md"
STATUS_META = ROOT / "docs" / "evidence" / "status_meta.json"
DOCS_ROOT = ROOT / "docs"

STALE_TEST_COUNT_EXCLUSIONS = frozenset(
    {
        DOCS_ROOT / "review" / "templates" / "readiness_report_review.json",
    }
)


def _git_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def test_live_extraction_summary_exists_and_parses() -> None:
    assert LIVE_EXTRACTION_SUMMARY.is_file(), (
        "docs/evidence/live_extraction_v0.2/summary.json is missing; "
        "run make record-live-extraction after make demo-live"
    )
    payload = json.loads(LIVE_EXTRACTION_SUMMARY.read_text(encoding="utf-8"))
    assert payload.get("schema_version") == "0.1"
    examples = payload.get("examples")
    assert isinstance(examples, list) and len(examples) >= 2


def _pytest_collection_count() -> int:
    import os
    import sys

    env = dict(os.environ)
    src = ROOT / "packages" / "fre_core" / "src"
    env["PYTHONPATH"] = f"{src}{os.pathsep}."
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"(\d+)\s+tests?\s+collected", completed.stdout)
    if not match:
        raise RuntimeError(f"Could not parse pytest collection output:\n{completed.stdout}")
    return int(match.group(1))


def _git_diff_paths(from_ref: str, to_ref: str) -> set[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", from_ref, to_ref],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line for line in completed.stdout.splitlines() if line}


def test_current_main_status_matches_head() -> None:
    assert STATUS_META.is_file(), (
        "docs/evidence/status_meta.json is missing; run make record-main-status"
    )
    assert CURRENT_MAIN_STATUS.is_file(), (
        "docs/evidence/current_main_status.md is missing; run make record-main-status"
    )

    meta = json.loads(STATUS_META.read_text(encoding="utf-8"))
    head = _git_head()
    recorded = meta.get("commit_sha")
    assert recorded, "status_meta.json must include commit_sha"

    status_text = CURRENT_MAIN_STATUS.read_text(encoding="utf-8")
    assert recorded in status_text
    assert meta.get("pytest_collection_count") == _pytest_collection_count()

    if recorded == head:
        return

    # Allow a docs-only status refresh commit on top of the recorded sprint SHA.
    evidence_only = {
        "docs/evidence/current_main_status.md",
        "docs/evidence/status_meta.json",
    }
    diff_paths = _git_diff_paths(recorded, head)
    assert diff_paths <= evidence_only, (
        f"status_meta commit_sha {recorded!r} != HEAD {head!r} and diff is not "
        f"evidence-only: {sorted(diff_paths)}; run make record-main-status"
    )


def test_docs_do_not_claim_stale_test_count_165() -> None:
    stale_pattern = re.compile(r"\b165\b")
    test_claim_pattern = re.compile(r"\b165\b.*\btests?\b|\btests?\b.*\b165\b", re.IGNORECASE)

    offenders: list[str] = []
    for path in sorted(DOCS_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".json"}:
            continue
        if path in STALE_TEST_COUNT_EXCLUSIONS:
            continue
        if "CHANGELOG" in path.name.upper():
            continue
        text = path.read_text(encoding="utf-8")
        if stale_pattern.search(text) and test_claim_pattern.search(text):
            offenders.append(path.relative_to(ROOT).as_posix())

    assert not offenders, f"Stale '165 tests' claims found in: {offenders}"
