"""Structured telemetry for model extraction calls."""

from __future__ import annotations

import hashlib
import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager

logger = logging.getLogger("fre_core.model_telemetry")


def hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


@contextmanager
def log_model_call(*, model: str, schema_name: str, prompt: str) -> Iterator[str]:
    prompt_hash = hash_prompt(prompt)
    start = time.perf_counter()
    logger.info(
        "model_call_start model=%s schema=%s prompt_hash=%s",
        model,
        schema_name,
        prompt_hash,
    )
    try:
        yield prompt_hash
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        logger.info(
            "model_call_end model=%s schema=%s prompt_hash=%s latency_ms=%.2f",
            model,
            schema_name,
            prompt_hash,
            elapsed_ms,
        )
