from pathlib import Path

import pytest

from fre_core.evaluation_agreement import cohens_kappa, jaccard_similarity, score_reviewer_agreement
from fre_core.review_workflow import load_review_submission
from fre_core.schemas import ReadinessReportReviewSubmission
from fre_core.validation import load_readiness_report

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "review_submissions"
GOLD_REPORT = ROOT / "benchmarks" / "readinessbench" / "gold" / "finite_tree_edge_count" / "readiness_report.json"


def test_jaccard_identical() -> None:
    assert jaccard_similarity(left=["a"], right=["a"]) == 1.0


def test_kappa_identical() -> None:
    assert cohens_kappa(left=["a", "b"], right=["a", "b"]) == 1.0


def test_agreement_fixtures() -> None:
    a = load_review_submission(FIXTURES / "finite_tree_reviewer_a.json")
    b = load_review_submission(FIXTURES / "finite_tree_reviewer_b.json")
    report = score_reviewer_agreement(submission_a=a, submission_b=b)
    assert report.unit_id == "finite_tree_edge_count"
    assert len(report.list_field_agreement) == 3


def test_agreement_unit_mismatch() -> None:
    base = ReadinessReportReviewSubmission.model_validate_json(
        (FIXTURES / "finite_tree_reviewer_a.json").read_text(encoding="utf-8")
    )
    report = load_readiness_report(GOLD_REPORT)
    other = base.model_copy(
        update={
            "unit_id": "other",
            "corrected_report": report.model_copy(update={"unit_id": "other"}),
        }
    )
    with pytest.raises(ValueError, match="Unit mismatch"):
        score_reviewer_agreement(submission_a=base, submission_b=other)
