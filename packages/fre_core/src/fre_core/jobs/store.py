"""SQLite-backed job metadata store."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from fre_core.jobs.schemas import JobRecord, JobStatus, JobType


def default_jobs_db_path() -> Path:
    configured = os.environ.get("FRE_JOBS_DB")
    if configured:
        return Path(configured)
    return Path(os.environ.get("FRE_ARTIFACT_DIR", "artifacts/generated")) / "jobs.db"


class JobStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or default_jobs_db_path()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _init_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    result_json TEXT,
                    error_message TEXT,
                    rq_job_id TEXT
                )
                """
            )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(tz=UTC)

    def create_job(self, *, job_type: JobType, request: dict[str, Any], job_id: str | None = None) -> JobRecord:
        now = self._now()
        record_id = job_id or str(uuid.uuid4())
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO jobs (id, job_type, status, created_at, updated_at, request_json) VALUES (?, ?, ?, ?, ?, ?)",
                (record_id, job_type.value, JobStatus.QUEUED.value, now.isoformat(), now.isoformat(), json.dumps(request)),
            )
        return self.get_job(record_id)

    def get_job(self, job_id: str) -> JobRecord:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return JobRecord(
            id=row["id"],
            job_type=JobType(row["job_type"]),
            status=JobStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            request=json.loads(row["request_json"]),
            result=json.loads(row["result_json"]) if row["result_json"] else None,
            error=row["error_message"],
        )

    def set_rq_job_id(self, job_id: str, rq_job_id: str) -> JobRecord:
        with self._connect() as connection:
            connection.execute(
                "UPDATE jobs SET rq_job_id = ?, updated_at = ? WHERE id = ?",
                (rq_job_id, self._now().isoformat(), job_id),
            )
        return self.get_job(job_id)

    def update_status(
        self,
        job_id: str,
        *,
        status: JobStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> JobRecord:
        now = self._now()
        with self._connect() as connection:
            connection.execute(
                "UPDATE jobs SET status = ?, updated_at = ?, result_json = ?, error_message = ? WHERE id = ?",
                (status.value, now.isoformat(), json.dumps(result) if result is not None else None, error, job_id),
            )
        return self.get_job(job_id)


_store: JobStore | None = None


def get_job_store() -> JobStore:
    global _store
    if _store is None:
        _store = JobStore()
    return _store


def reset_job_store(store: JobStore | None = None) -> None:
    global _store
    _store = store
