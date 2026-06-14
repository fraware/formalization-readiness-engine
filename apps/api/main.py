"""Minimal FastAPI backend for artifact validation and mathlib alignment."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from fre_core.mathlib_alignment import (
    align_readiness_report,
    suggest_import_modules_from_alignment,
)
from fre_core.mathlib_index import load_index, trimmed_index_path
from fre_core.review_workflow import ReviewWorkflowError, validate_review_submission
from fre_core.schemas import AlignmentResult, ReadinessReport, ReadinessReportReviewSubmission
from fre_core.validation import ArtifactValidationError, validate_readiness_report

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_INDEX_PATH = trimmed_index_path(repo_root=_REPO_ROOT)

_EXAMPLES: dict[str, dict[str, str]] = {
    "finite_tree": {
        "unit": "examples/finite_tree/unit.json",
        "readiness_report": "examples/finite_tree/readiness_report.json",
        "proofgraph": "examples/finite_tree/proofgraph.json",
        "atlas_record": "examples/finite_tree/atlas_record.json",
        "leantask": "examples/finite_tree/leantask.json",
    },
    "category_theory_pullback": {
        "unit": "examples/category_theory_pullback/unit.json",
        "readiness_report": "examples/category_theory_pullback/readiness_report.json",
        "proofgraph": "examples/category_theory_pullback/proofgraph.json",
        "atlas_record": "examples/category_theory_pullback/atlas_record.json",
        "leantask": "examples/category_theory_pullback/leantask.json",
    },
}


class ExampleMetadata(BaseModel):
    name: str
    artifacts: dict[str, str]


class ValidationResult(BaseModel):
    valid: bool
    unit_id: str | None = None
    message: str | None = None
    issues: list[str] = Field(default_factory=list)


class AlignReadinessReportRequest(BaseModel):
    report: ReadinessReport
    unit: dict[str, Any] | None = None
    confirmed_full_names: list[str] = Field(default_factory=list)
    index_path: str | None = None


class PromoteAlignmentRequest(BaseModel):
    report: ReadinessReport
    unit: dict[str, Any] | None = None
    confirmed_full_names: list[str] = Field(default_factory=list)
    index_path: str | None = None


class PromoteAlignmentResponse(BaseModel):
    unit_id: str
    alignment: AlignmentResult
    confirmed_alignment_full_names: list[str]
    suggested_import_modules: list[str]


def _resolve_repo_path(relative_path: str) -> Path:
    candidate = (_REPO_ROOT / relative_path).resolve()
    try:
        candidate.relative_to(_REPO_ROOT.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Path escapes repository root: {relative_path}") from exc
    return candidate


def create_app() -> FastAPI:
    app = FastAPI(
        title="Formalization Readiness Engine API",
        version="0.1.0",
        description="Artifact-first validation and alignment endpoints for the review workflow.",
    )

    cors_origins = os.environ.get("FRE_API_CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in cors_origins.split(",") if origin.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/examples")
    def list_examples() -> list[str]:
        return sorted(_EXAMPLES)

    @app.get("/examples/{name}", response_model=ExampleMetadata)
    def get_example(name: str) -> ExampleMetadata:
        artifacts = _EXAMPLES.get(name)
        if artifacts is None:
            raise HTTPException(status_code=404, detail=f"Unknown example: {name}")
        return ExampleMetadata(name=name, artifacts=artifacts)

    @app.post("/validate/readiness-report", response_model=ValidationResult)
    def validate_readiness_report_endpoint(report: ReadinessReport) -> ValidationResult:
        try:
            validate_readiness_report(report)
        except ArtifactValidationError as exc:
            return ValidationResult(
                valid=False,
                unit_id=report.unit_id,
                message="Readiness report failed semantic validation.",
                issues=[issue.message for issue in exc.issues],
            )
        return ValidationResult(valid=True, unit_id=report.unit_id, message="Readiness report is valid.")

    @app.post("/validate/review-submission", response_model=ValidationResult)
    def validate_review_submission_endpoint(submission: ReadinessReportReviewSubmission) -> ValidationResult:
        try:
            validate_review_submission(submission)
        except ReviewWorkflowError as exc:
            return ValidationResult(
                valid=False,
                unit_id=submission.unit_id,
                message=str(exc),
            )
        return ValidationResult(
            valid=True,
            unit_id=submission.unit_id,
            message="Review submission passed workflow validation.",
        )

    @app.post("/align/readiness-report", response_model=AlignmentResult)
    def align_readiness_report_endpoint(request: AlignReadinessReportRequest) -> AlignmentResult:
        index_path = _resolve_repo_path(request.index_path) if request.index_path else _DEFAULT_INDEX_PATH
        if not index_path.exists():
            raise HTTPException(status_code=404, detail=f"Index not found: {index_path.as_posix()}")

        index = load_index(index_path)
        unit = None
        if request.unit is not None:
            unit = load_unit_from_payload(request.unit)

        return align_readiness_report(
            report=request.report,
            index=index,
            unit=unit,
            confirmed_full_names=frozenset(request.confirmed_full_names),
        )

    @app.post("/review/promote-alignment", response_model=PromoteAlignmentResponse)
    def promote_alignment_endpoint(request: PromoteAlignmentRequest) -> PromoteAlignmentResponse:
        index_path = _resolve_repo_path(request.index_path) if request.index_path else _DEFAULT_INDEX_PATH
        if not index_path.exists():
            raise HTTPException(status_code=404, detail=f"Index not found: {index_path.as_posix()}")

        index = load_index(index_path)
        unit = None
        if request.unit is not None:
            unit = load_unit_from_payload(request.unit)

        alignment = align_readiness_report(
            report=request.report,
            index=index,
            unit=unit,
            confirmed_full_names=frozenset(request.confirmed_full_names),
        )
        confirmed_names = [candidate.full_name for candidate in alignment.confirmed]
        suggested_imports = suggest_import_modules_from_alignment(alignment=alignment)
        return PromoteAlignmentResponse(
            unit_id=request.report.unit_id,
            alignment=alignment,
            confirmed_alignment_full_names=confirmed_names,
            suggested_import_modules=suggested_imports,
        )

    return app


def load_unit_from_payload(payload: dict[str, Any]):
    from fre_core.schemas import TheoremProofUnit

    return TheoremProofUnit.model_validate(payload)


app = create_app()
