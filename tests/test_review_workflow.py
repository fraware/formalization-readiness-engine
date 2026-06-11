from pathlib import Path

import pytest

from fre_core.review_workflow import (
    ReviewWorkflowError,
    load_changelog_entries,
    load_review_submission,
    validate_changelog_entries,
    validate_review_submission,
)
from fre_core.schemas import ReadinessReportReviewSubmission, ReviewStatus

ROOT = Path(__file__).resolve().parents[1]
REVIEW_TEMPLATE = ROOT / "docs" / "review" / "templates" / "readiness_report_review.json"
GOLD_CHANGELOG = ROOT / "benchmarks" / "readinessbench" / "gold" / "changelog.jsonl"


def test_review_submission_template_loads_and_validates() -> None:
    submission = load_review_submission(REVIEW_TEMPLATE)
    assert isinstance(submission, ReadinessReportReviewSubmission)
    assert submission.unit_id == "finite_tree_edge_count"
    assert submission.tier_promotion == "gold"
    assert submission.review_status == ReviewStatus.EXPERT_REVIEWED
    validate_review_submission(submission)


def test_review_submission_rejects_tier_status_mismatch() -> None:
    submission = load_review_submission(REVIEW_TEMPLATE)
    submission = submission.model_copy(update={"review_status": ReviewStatus.HUMAN_REVIEWED})

    with pytest.raises(ReviewWorkflowError, match="tier_promotion='gold'"):
        validate_review_submission(submission)


def test_review_submission_requires_corrections_when_lists_inaccurate() -> None:
    submission = load_review_submission(REVIEW_TEMPLATE)
    submission = submission.model_copy(
        update={
            "list_fields_accurate": False,
            "corrected_report_path": None,
            "corrected_report": None,
        }
    )

    with pytest.raises(ReviewWorkflowError, match="corrected_report"):
        validate_review_submission(submission)


def test_gold_changelog_jsonl_validates() -> None:
    entries = load_changelog_entries(GOLD_CHANGELOG)
    validate_changelog_entries(entries)

    assert entries[0].item_id == "finite_tree_edge_count_gold"
    assert entries[0].fields_changed
