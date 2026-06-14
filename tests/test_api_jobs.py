from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from apps.api.main import create_app
from fre_core.jobs import JobStatus, JobStore, JobType, reset_job_queue, reset_job_store
from fre_core.jobs.queue import InlineJobQueue


class FakeJobQueue:
    def __init__(self) -> None:
        self.enqueued: list[dict[str, Any]] = []

    def enqueue(self, *, job_id: str, job_type: JobType, payload: dict[str, Any]) -> str:
        self.enqueued.append({"job_id": job_id, "job_type": job_type, "payload": payload})
        return f"fake-{job_id}"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    reset_job_store(JobStore(db_path=tmp_path / "jobs.db"))
    reset_job_queue(FakeJobQueue())
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_job_store(None)
    reset_job_queue(None)


def test_post_jobs_extract(client: TestClient) -> None:
    r = client.post("/jobs/extract", json={"unit_path": "examples/finite_tree/unit.json"})
    assert r.status_code == 200
    assert r.json()["job_type"] == "extract_report"


def test_post_jobs_extract_enqueues(client: TestClient) -> None:
    from fre_core.jobs import get_job_queue

    q = get_job_queue()
    assert isinstance(q, FakeJobQueue)
    client.post("/jobs/extract", json={"unit_path": "examples/finite_tree/unit.json"})
    assert len(q.enqueued) == 1


def test_post_jobs_extract_rejects_escape(client: TestClient) -> None:
    assert client.post("/jobs/extract", json={"unit_path": "../../etc/passwd"}).status_code == 400


def test_get_job_unknown(client: TestClient) -> None:
    assert client.get("/jobs/missing").status_code == 404


def test_get_job_status(client: TestClient) -> None:
    from fre_core.jobs import get_job_store

    get_job_store().create_job(job_type=JobType.EXTRACT_REPORT, request={}, job_id="j1")
    get_job_store().update_status("j1", status=JobStatus.COMPLETED, result={"ok": True})
    body = client.get("/jobs/j1").json()
    assert body["status"] == "completed"


def test_run_baselines_inline(tmp_path: Path) -> None:
    reset_job_store(JobStore(db_path=tmp_path / "jobs.db"))
    from fre_core.jobs import get_job_store, run_baselines_job

    rec = get_job_store().create_job(
        job_type=JobType.RUN_BASELINES,
        request={"catalog_path": "corpus/catalog.json", "output_dir": "artifacts/generated/baselines"},
        job_id="b1",
    )
    run_baselines_job(rec.id, rec.request)
    assert get_job_store().get_job("b1").status == JobStatus.COMPLETED
    reset_job_store(None)
