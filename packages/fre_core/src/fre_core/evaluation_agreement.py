"""Inter-annotator agreement metrics for review submissions."""

from __future__ import annotations

from fre_core.evaluation import _normalize_label
from fre_core.schemas import (
    ReadinessReportReviewSubmission,
    ReviewerAgreementFieldScore,
    ReviewerAgreementReport,
    UsefulnessRubricScores,
)

LIST_FIELD_NAMES = ("existing_theorem_candidates", "constructive_path", "blockers")
RUBRIC_FIELD_NAMES = (
    "source_fidelity",
    "actionability",
    "library_alignment",
    "blocker_specificity",
    "path_clarity",
)


def _label_set(values: list[str]) -> set[str]:
    return {_normalize_label(item) for item in values if item.strip()}


def jaccard_similarity(*, left: list[str], right: list[str]) -> float:
    left_set, right_set = _label_set(left), _label_set(right)
    if not left_set and not right_set:
        return 1.0
    union = left_set | right_set
    return len(left_set & right_set) / len(union) if union else 1.0


def cohens_kappa(*, left: list[str], right: list[str]) -> float:
    left_set, right_set = _label_set(left), _label_set(right)
    labels = sorted(left_set | right_set)
    if not labels:
        return 1.0
    agree = left_yes = right_yes = 0
    for label in labels:
        lp, rp = label in left_set, label in right_set
        if lp == rp:
            agree += 1
        left_yes += int(lp)
        right_yes += int(rp)
    n = len(labels)
    p_o = agree / n
    p_l, p_r = left_yes / n, right_yes / n
    p_e = p_l * p_r + (1 - p_l) * (1 - p_r)
    return 1.0 if p_e == 1.0 else (p_o - p_e) / (1 - p_e)


def score_rubric_cohens_kappa(*, left: UsefulnessRubricScores, right: UsefulnessRubricScores) -> float:
    left_scores = [getattr(left, name) for name in RUBRIC_FIELD_NAMES]
    right_scores = [getattr(right, name) for name in RUBRIC_FIELD_NAMES]
    n = len(RUBRIC_FIELD_NAMES)
    p_o = sum(a == b for a, b in zip(left_scores, right_scores, strict=True)) / n
    p_e = sum(left_scores.count(c) / n * right_scores.count(c) / n for c in sorted(set(left_scores + right_scores)))
    return 1.0 if p_e == 1.0 else (p_o - p_e) / (1 - p_e)


def score_reviewer_agreement(
    *,
    submission_a: ReadinessReportReviewSubmission,
    submission_b: ReadinessReportReviewSubmission,
) -> ReviewerAgreementReport:
    if submission_a.unit_id != submission_b.unit_id:
        raise ValueError(f"Unit mismatch: {submission_a.unit_id!r} vs {submission_b.unit_id!r}.")
    if submission_a.corrected_report is None or submission_b.corrected_report is None:
        raise ValueError("Both submissions must include corrected_report.")
    list_scores: list[ReviewerAgreementFieldScore] = []
    for field_name in LIST_FIELD_NAMES:
        left_values = getattr(submission_a.corrected_report, field_name)
        right_values = getattr(submission_b.corrected_report, field_name)
        list_scores.append(
            ReviewerAgreementFieldScore(
                field_name=field_name,
                jaccard=jaccard_similarity(left=left_values, right=right_values),
                exact_match=_label_set(left_values) == _label_set(right_values),
                cohens_kappa=round(cohens_kappa(left=left_values, right=right_values), 6),
            )
        )
    mean_j = round(sum(s.jaccard for s in list_scores) / len(list_scores), 6)
    exact = sum(1 for s in list_scores if s.exact_match)
    return ReviewerAgreementReport(
        unit_id=submission_a.unit_id,
        reviewer_a=submission_a.reviewer_id,
        reviewer_b=submission_b.reviewer_id,
        list_field_agreement=list_scores,
        rubric_cohens_kappa=round(score_rubric_cohens_kappa(left=submission_a.rubric_scores, right=submission_b.rubric_scores), 6),
        mean_list_jaccard=mean_j,
        overall_percent_agreement=round(exact / len(list_scores) * 100, 2),
    )
