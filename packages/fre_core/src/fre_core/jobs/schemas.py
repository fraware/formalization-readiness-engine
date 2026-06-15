"""Pydantic models for async job requests and responses."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobType(str, Enum):
    EXTRACT_REPORT = "extract_report"
    RUN_BASELINES = "run_baselines"
    CHECK_LEAN = "check_lean"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractReportJobRequest(BaseModel):
    unit_path: str
    output_path: str | None = None
    model: str | None = None
    enrich_candidates: bool = False
    index_suggestions_in_prompt: bool = False
    index_path: str | None = None
    candidate_top_k: int = 5


class RunBaselinesJobRequest(BaseModel):
    catalog_path: str = "benchmarks/baselines/manifest.json"
    output_dir: str = "artifacts/generated/baselines"
    conditions: list[str] = Field(default_factory=lambda: ["direct"])
    unit_ids: list[str] | None = None
    model: str | None = None


class CheckLeanJobRequest(BaseModel):
    lean_path: str
    project_dir: str = "lean"
    timeout_seconds: int = 60


class JobRecord(BaseModel):
    id: str
    job_type: JobType
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    request: dict[str, Any]
    result: dict[str, Any] | None = None
    error: str | None = None


class JobCreateResponse(BaseModel):
    id: str
    job_type: JobType
    status: JobStatus


class JobStatusResponse(BaseModel):
    id: str
    job_type: JobType
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    result: dict[str, Any] | None = None
    error: str | None = None
