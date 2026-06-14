"""Worker task implementations for async jobs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fre_core.jobs.schemas import JobStatus
from fre_core.jobs.store import get_job_store


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "apps").is_dir() and (parent / "packages").is_dir():
            return parent
    return current.parents[5]


def resolve_repo_path(relative_path: str) -> Path:
    root = _repo_root()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Path escapes repository root: {relative_path}") from exc
    return candidate


def run_extract_report_job(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    get_job_store().update_status(job_id, status=JobStatus.RUNNING)
    try:
        from fre_core.extraction import extract_readiness_report
        from fre_core.mathlib_index import default_index_path, load_index
        from fre_core.openai_responses_provider import OpenAIResponsesProvider
        from fre_core.validation import load_unit

        unit = load_unit(resolve_repo_path(payload["unit_path"]))
        index = None
        if payload.get("enrich_candidates"):
            index_path = payload.get("index_path")
            index = load_index(resolve_repo_path(index_path) if index_path else default_index_path())
        report = extract_readiness_report(
            unit=unit,
            model_client=OpenAIResponsesProvider(model=payload.get("model")),
            enrich_candidates=bool(payload.get("enrich_candidates")),
            index=index,
            candidate_top_k=int(payload.get("candidate_top_k", 5)),
        )
        output_path = payload.get("output_path") or f"artifacts/generated/{unit.unit_id}/readiness_report.model.json"
        out = resolve_repo_path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        result = {"unit_id": report.unit_id, "output_path": output_path, "report": json.loads(report.model_dump_json())}
        get_job_store().update_status(job_id, status=JobStatus.COMPLETED, result=result)
        return result
    except Exception as exc:  # noqa: BLE001
        get_job_store().update_status(job_id, status=JobStatus.FAILED, error=str(exc))
        raise


def run_check_lean_job(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    get_job_store().update_status(job_id, status=JobStatus.RUNNING)
    try:
        from fre_core.lean_runner import check_lean_file

        result_obj = check_lean_file(
            path=resolve_repo_path(payload["lean_path"]),
            cwd=resolve_repo_path(payload.get("project_dir", "lean")),
            timeout_seconds=int(payload.get("timeout_seconds", 60)),
        )
        result = {
            "lean_path": payload["lean_path"],
            "passed": result_obj.passed,
            "returncode": result_obj.returncode,
            "stdout": result_obj.stdout,
            "stderr": result_obj.stderr,
        }
        status = JobStatus.COMPLETED if result_obj.passed else JobStatus.FAILED
        get_job_store().update_status(job_id, status=status, result=result, error=None if result_obj.passed else result_obj.stderr)
        return result
    except Exception as exc:  # noqa: BLE001
        get_job_store().update_status(job_id, status=JobStatus.FAILED, error=str(exc))
        raise


def run_baselines_job(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    get_job_store().update_status(job_id, status=JobStatus.RUNNING)
    try:
        catalog_path = resolve_repo_path(payload.get("catalog_path", "corpus/catalog.json"))
        output_dir = resolve_repo_path(payload.get("output_dir", "artifacts/generated/baselines"))
        output_dir.mkdir(parents=True, exist_ok=True)
        result = {
            "catalog_path": payload.get("catalog_path", "corpus/catalog.json"),
            "output_dir": payload.get("output_dir", "artifacts/generated/baselines"),
            "conditions": payload.get("conditions", ["direct"]),
            "message": "Baseline harness v0 stub until Wave 3 CLI lands.",
            "catalog_exists": catalog_path.exists(),
        }
        manifest = output_dir / f"{job_id}_run_manifest.json"
        manifest.write_text(json.dumps(result, indent=2), encoding="utf-8")
        result["run_manifest_path"] = manifest.relative_to(_repo_root()).as_posix()
        get_job_store().update_status(job_id, status=JobStatus.COMPLETED, result=result)
        return result
    except Exception as exc:  # noqa: BLE001
        get_job_store().update_status(job_id, status=JobStatus.FAILED, error=str(exc))
        raise
