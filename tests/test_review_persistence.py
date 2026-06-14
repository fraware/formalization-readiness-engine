from pathlib import Path

import pytest

from fre_core.review_persistence import (
    ReviewPersistenceError,
    ReviewWriteDisabledError,
    compute_report_diff_summary,
    persist_review_submission,
    report_content_hash,
)
from fre_core.review_workflow import load_review_submission
from fre_core.schemas import ReviewStatus
from fre_core.validation import load_readiness_report

ROOT = Path(__file__).resolve().parents[1]
REVIEW_TEMPLATE = ROOT / "docs" / "review" / "templates" / "readiness_report_review.json"
GOLD_REPORT = ROOT / "benchmarks" / "readinessbench" / "gold" / "finite_tree_edge_count" / "readiness_report.json"


def _silver_submission(*, report):
    return load_review_submission(REVIEW_TEMPLATE).model_copy(
        update={
            "item_id": "finite_tree_edge_count_silver",
            "reviewer_id": "reviewer.test",
            "review_date": "2026-06-14",
            "tier_promotion": "silver",
            "review_status": ReviewStatus.HUMAN_REVIEWED,
            "corrected_report_path": None,
            "corrected_report": report.model_copy(update={"review_status": ReviewStatus.HUMAN_REVIEWED}),
            "list_fields_accurate": False,
        }
    )


def test_report_content_hash_is_stable() -> None:
    report = load_readiness_report(GOLD_REPORT)
    assert report_content_hash(report) == report_content_hash(report)


def test_compute_report_diff_summary_detects_changes() -> None:
    before = load_readiness_report(GOLD_REPORT)
    after = before.model_copy(update={"blockers": before.blockers + ["extra blocker"]})
    assert "blockers" in compute_report_diff_summary(before=before, after=after)


def test_persist_requires_write_enabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("FRE_REVIEW_WRITE_ENABLED", raising=False)
    with pytest.raises(ReviewWriteDisabledError):
        persist_review_submission(
            submission=_silver_submission(report=load_readiness_report(GOLD_REPORT)),
            benchmark_root=tmp_path,
            repo_root=ROOT,
        )


def test_persist_writes_silver(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FRE_REVIEW_WRITE_ENABLED", "1")
    result = persist_review_submission(
        submission=_silver_submission(report=load_readiness_report(GOLD_REPORT)),
        benchmark_root=tmp_path,
        repo_root=ROOT,
    )
    assert result.tier == "silver"
    assert (tmp_path / result.report_path).exists()
    assert (tmp_path / result.edit_record_path).exists()


def test_persist_appends_gold_changelog(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FRE_REVIEW_WRITE_ENABLED", "1")
    report = load_readiness_report(GOLD_REPORT)
    submission = load_review_submission(REVIEW_TEMPLATE).model_copy(
        update={"corrected_report_path": None, "corrected_report": report, "list_fields_accurate": False, "notes": "Gold test."}
    )
    result = persist_review_submission(submission=submission, benchmark_root=tmp_path, repo_root=ROOT)
    assert result.changelog_appended
    assert "Gold test." in (tmp_path / "gold" / "changelog.jsonl").read_text(encoding="utf-8")


def test_persist_rejects_missing_tier(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FRE_REVIEW_WRITE_ENABLED", "1")
    submission = _silver_submission(report=load_readiness_report(GOLD_REPORT)).model_copy(update={"tier_promotion": None})
    with pytest.raises(ReviewPersistenceError, match="tier_promotion"):
        persist_review_submission(submission=submission, benchmark_root=tmp_path, repo_root=ROOT)
