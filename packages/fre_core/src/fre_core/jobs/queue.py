"""RQ queue integration for async jobs."""

from __future__ import annotations

import os
from typing import Any

from fre_core.jobs.schemas import JobType
from fre_core.jobs.store import get_job_store
from fre_core.jobs.tasks import run_baselines_job, run_check_lean_job, run_extract_report_job

TASK_REGISTRY = {
    JobType.EXTRACT_REPORT: run_extract_report_job,
    JobType.RUN_BASELINES: run_baselines_job,
    JobType.CHECK_LEAN: run_check_lean_job,
}


class JobQueue:
    def __init__(self, redis_url_value: str | None = None, queue: str | None = None) -> None:
        self._redis_url = redis_url_value or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._queue_name = queue or os.environ.get("FRE_RQ_QUEUE", "fre-jobs")
        self._queue = None

    def _get_queue(self):
        if self._queue is None:
            from redis import Redis
            from rq import Queue

            self._queue = Queue(self._queue_name, connection=Redis.from_url(self._redis_url))
        return self._queue

    def enqueue(self, *, job_id: str, job_type: JobType, payload: dict[str, Any]) -> str:
        rq_job = self._get_queue().enqueue(TASK_REGISTRY[job_type], job_id, payload)
        get_job_store().set_rq_job_id(job_id, rq_job.id)
        return rq_job.id


class InlineJobQueue:
    def enqueue(self, *, job_id: str, job_type: JobType, payload: dict[str, Any]) -> str:
        TASK_REGISTRY[job_type](job_id, payload)
        return f"inline-{job_id}"


_queue = None


def get_job_queue():
    global _queue
    if _queue is None:
        inline = os.environ.get("FRE_JOBS_INLINE", "").lower() in {"1", "true", "yes"}
        _queue = InlineJobQueue() if inline else JobQueue()
    return _queue


def reset_job_queue(queue=None) -> None:
    global _queue
    _queue = queue
