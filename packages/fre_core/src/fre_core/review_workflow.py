"""Validation helpers for external review submissions and gold changelog entries."""

from __future__ import annotations

import json
from pathlib import Path

from fre_core.schemas import (
    GoldArtifactChangelogEntry,
    ReadinessReportReviewSubmission,
    ReviewStatus,
)

TIER_REQUIRED_REVIEW_STATUS = {
    "silver": ReviewStatus.HUMAN_REVIEWED,
    "gold": ReviewStatus.EXPERT_REVIEWED,
}


class ReviewWorkflowError(ValueError):
    """Raised when a review submission or changelog entry fails workflow checks."""


def load_review_submission(path: Path) -> ReadinessReportReviewSubmission:
    return ReadinessReportReviewSubmission.model_validate_json(path.read_text(encoding="utf-8"))


def validate_review_submission(submission: ReadinessReportReviewSubmission) -> None:
    """Validate tier promotion, review status, and corrected report alignment."""
    if submission.tier_promotion is not None:
        required_status = TIER_REQUIRED_REVIEW_STATUS[submission.tier_promotion]
        if submission.review_status != required_status:
            raise ReviewWorkflowError(
                f"tier_promotion='{submission.tier_promotion}' requires "
                f"review_status='{required_status.value}', got "
                f"'{submission.review_status.value}'."
            )

    if submission.corrected_report is not None and submission.corrected_report.unit_id != submission.unit_id:
        raise ReviewWorkflowError(
            f"corrected_report.unit_id='{submission.corrected_report.unit_id}' "
            f"does not match submission.unit_id='{submission.unit_id}'."
        )

    if submission.corrected_report is not None:
        if submission.corrected_report.review_status != submission.review_status:
            raise ReviewWorkflowError(
                "corrected_report.review_status must match submission.review_status."
            )

    has_corrections = submission.corrected_report is not None or submission.corrected_report_path is not None
    if not has_corrections and not submission.list_fields_accurate:
        raise ReviewWorkflowError(
            "Provide corrected_report or corrected_report_path when list_fields_accurate is false."
        )


def load_changelog_entries(path: Path) -> list[GoldArtifactChangelogEntry]:
    entries: list[GoldArtifactChangelogEntry] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ReviewWorkflowError(f"Invalid JSON on line {line_number} of {path}: {exc}") from exc
        entries.append(GoldArtifactChangelogEntry.model_validate(payload))
    return entries


def validate_changelog_entries(entries: list[GoldArtifactChangelogEntry]) -> None:
    if not entries:
        raise ReviewWorkflowError("Gold changelog must contain at least one entry.")

    seen_dates_and_items: set[tuple[str, str, str]] = set()
    for entry in entries:
        if not entry.summary.strip():
            raise ReviewWorkflowError(f"Changelog entry for item_id='{entry.item_id}' needs a summary.")
        if not entry.fields_changed:
            raise ReviewWorkflowError(
                f"Changelog entry for item_id='{entry.item_id}' must list fields_changed."
            )
        key = (entry.date, entry.item_id, entry.summary)
        if key in seen_dates_and_items:
            raise ReviewWorkflowError(
                f"Duplicate changelog entry for item_id='{entry.item_id}' on date='{entry.date}'."
            )
        seen_dates_and_items.add(key)
