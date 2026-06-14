from __future__ import annotations

from fastapi import APIRouter, HTTPException

from fre_core.jobs import (
    CheckLeanJobRequest,
    ExtractReportJobRequest,
    JobCreateResponse,
    JobStatusResponse,
    JobType,
    RunBaselinesJobRequest,
    get_job_queue,
    get_job_store,
    resolve_repo_path,
)
from fre_core.jobs.schemas import JobRecord

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _status(record: JobRecord) -> JobStatusResponse:
    return JobStatusResponse(
        id=record.id,
        job_type=record.job_type,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
        result=record.result,
        error=record.error,
    )


def _enqueue(job_type: JobType, payload: dict) -> JobCreateResponse:
    record = get_job_store().create_job(job_type=job_type, request=payload)
    get_job_queue().enqueue(job_id=record.id, job_type=job_type, payload=payload)
    return JobCreateResponse(id=record.id, job_type=record.job_type, status=record.status)


@router.post("/extract", response_model=JobCreateResponse)
def submit_extract_job(request: ExtractReportJobRequest) -> JobCreateResponse:
    try:
        resolve_repo_path(request.unit_path)
        if request.index_path:
            resolve_repo_path(request.index_path)
        if request.output_path:
            resolve_repo_path(request.output_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _enqueue(JobType.EXTRACT_REPORT, request.model_dump(mode="json"))


@router.post("/check-lean", response_model=JobCreateResponse)
def submit_check_lean_job(request: CheckLeanJobRequest) -> JobCreateResponse:
    try:
        resolve_repo_path(request.lean_path)
        resolve_repo_path(request.project_dir)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _enqueue(JobType.CHECK_LEAN, request.model_dump(mode="json"))


@router.post("/run-baselines", response_model=JobCreateResponse)
def submit_run_baselines_job(request: RunBaselinesJobRequest) -> JobCreateResponse:
    try:
        resolve_repo_path(request.catalog_path)
        resolve_repo_path(request.output_dir)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _enqueue(JobType.RUN_BASELINES, request.model_dump(mode="json"))


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    try:
        return _status(get_job_store().get_job(job_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown job: {job_id}") from exc
