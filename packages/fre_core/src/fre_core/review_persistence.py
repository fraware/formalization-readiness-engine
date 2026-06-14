"""Persist validated review submissions to ReadinessBench tiers."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from fre_core.benchmark import default_benchmark_root, validate_review_status_for_tier
from fre_core.review_workflow import ReviewWorkflowError, validate_review_submission
from fre_core.schemas import (
    BenchmarkTier,
    GoldArtifactChangelogEntry,
    ReadinessReport,
    ReadinessReportReviewSubmission,
    ReviewEditRecord,
)
from fre_core.validation import ArtifactValidationError, load_readiness_report, validate_readiness_report

WRITE_ENABLED_ENV = "FRE_REVIEW_WRITE_ENABLED"
GOLD_CHANGELOG_RELATIVE = "gold/changelog.jsonl"


class ReviewPersistenceError(ValueError):
    """Raised when a review submission cannot be persisted."""


class ReviewWriteDisabledError(ReviewPersistenceError):
    """Raised when filesystem write-back is disabled."""


@dataclass(frozen=True)
class ReviewPersistResult:
    unit_id: str
    tier: str | None
    report_path: str | None
    edit_record_path: str | None
    submission_path: str | None
    changelog_appended: bool
    parent_report_hash: str | None
    corrected_report_hash: str


def is_review_write_enabled() -> bool:
    return os.environ.get(WRITE_ENABLED_ENV, "").strip() == "1"


def require_review_write_enabled() -> None:
    if not is_review_write_enabled():
        raise ReviewWriteDisabledError(
            f"Review write-back is disabled. Set {WRITE_ENABLED_ENV}=1 to enable filesystem writes."
        )


def report_content_hash(report: ReadinessReport) -> str:
    return hashlib.sha256(report.model_dump_json().encode("utf-8")).hexdigest()


def _resolve_repo_path(repo_root: Path, relative_path: str) -> Path:
    candidate = (repo_root / relative_path).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ReviewPersistenceError(f"Path escapes repository root: {relative_path}") from exc
    return candidate


def resolve_corrected_report(*, submission: ReadinessReportReviewSubmission, repo_root: Path) -> ReadinessReport:
    if submission.corrected_report is not None:
        return submission.corrected_report
    if submission.corrected_report_path is not None:
        report_path = _resolve_repo_path(repo_root, submission.corrected_report_path)
        if not report_path.exists():
            raise ReviewPersistenceError(f"corrected_report_path not found: {submission.corrected_report_path}")
        return load_readiness_report(report_path)
    raise ReviewPersistenceError("Submission must include corrected_report or corrected_report_path.")


def compute_report_diff_summary(*, before: ReadinessReport | None, after: ReadinessReport) -> list[str]:
    if before is None:
        return ["initial_submission"]
    changed: list[str] = []
    for name in ("statement_readiness", "context_readiness", "notation_readiness", "dependency_readiness"):
        if getattr(before, name).model_dump() != getattr(after, name).model_dump():
            changed.append(name)
    for field_name in (
        "existing_theorem_candidates",
        "constructive_path",
        "blockers",
        "recommended_next_action",
        "review_status",
    ):
        if getattr(before, field_name) != getattr(after, field_name):
            changed.append(field_name)
    return changed or ["unchanged"]


def persist_review_submission(
    *,
    submission: ReadinessReportReviewSubmission,
    benchmark_root: Path | None = None,
    repo_root: Path | None = None,
) -> ReviewPersistResult:
    require_review_write_enabled()
    root = repo_root or Path(__file__).resolve().parents[4]
    bench = benchmark_root or default_benchmark_root(repo_root=root)
    try:
        validate_review_submission(submission)
    except ReviewWorkflowError as exc:
        raise ReviewPersistenceError(str(exc)) from exc
    if submission.tier_promotion is None:
        raise ReviewPersistenceError("tier_promotion is required for review write-back.")
    corrected = resolve_corrected_report(submission=submission, repo_root=root)
    try:
        validate_readiness_report(corrected)
    except ArtifactValidationError as exc:
        raise ReviewPersistenceError(str(exc)) from exc
    validate_review_status_for_tier(
        tier=BenchmarkTier(submission.tier_promotion),
        review_status=corrected.review_status,
        context="corrected_report",
    )
    if corrected.unit_id != submission.unit_id:
        raise ReviewPersistenceError("corrected_report.unit_id does not match submission.unit_id.")
    parent_path = bench / submission.tier_promotion / submission.unit_id / "readiness_report.json"
    parent_report = load_readiness_report(parent_path) if parent_path.exists() else None
    parent_hash = report_content_hash(parent_report) if parent_report else None
    corrected_hash = report_content_hash(corrected)
    diff_summary = compute_report_diff_summary(before=parent_report, after=corrected)
    timestamp = datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    edit_id = f"{timestamp.replace(':', '').replace('-', '')}_{corrected_hash[:8]}"
    submission_rel = f"edits/{submission.unit_id}/submission_{edit_id}.json"
    edit_rel = f"edits/{submission.unit_id}/edit_{edit_id}.json"
    report_rel = f"{submission.tier_promotion}/{submission.unit_id}/readiness_report.json"
    for rel, payload in (
        (submission_rel, submission.model_dump(mode="json")),
        (report_rel, corrected.model_dump(mode="json")),
        (
            edit_rel,
            ReviewEditRecord(
                edit_id=edit_id,
                unit_id=submission.unit_id,
                editor=submission.reviewer_id,
                timestamp=timestamp,
                parent_report_hash=parent_hash,
                corrected_report_hash=corrected_hash,
                diff_summary=diff_summary,
                tier_promotion=submission.tier_promotion,
                review_submission_path=submission_rel,
            ).model_dump(mode="json"),
        ),
    ):
        path = bench / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    changelog_appended = False
    if submission.tier_promotion == "gold":
        changelog_path = bench / GOLD_CHANGELOG_RELATIVE
        changelog_path.parent.mkdir(parents=True, exist_ok=True)
        entry = GoldArtifactChangelogEntry(
            date=submission.review_date,
            item_id=submission.item_id or f"{submission.unit_id}_gold",
            reviewer_id=submission.reviewer_id,
            summary=submission.notes or f"Gold review write-back for unit {submission.unit_id}.",
            fields_changed=diff_summary,
            review_submission_path=submission_rel,
        )
        with changelog_path.open("a", encoding="utf-8") as handle:
            handle.write(entry.model_dump_json() + "\n")
        changelog_appended = True
    return ReviewPersistResult(
        unit_id=submission.unit_id,
        tier=submission.tier_promotion,
        report_path=report_rel,
        edit_record_path=edit_rel,
        submission_path=submission_rel,
        changelog_appended=changelog_appended,
        parent_report_hash=parent_hash,
        corrected_report_hash=corrected_hash,
    )
