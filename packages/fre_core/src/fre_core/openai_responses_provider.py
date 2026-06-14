"""OpenAI Responses provider for schema-constrained extraction."""

from __future__ import annotations

import os
import time
from typing import TypeVar

from pydantic import BaseModel

from fre_core.model_client import ModelClientError
from fre_core.model_telemetry import log_model_call

ModelT = TypeVar("ModelT", bound=BaseModel)

_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def _max_retries() -> int:
    raw = os.getenv("FRE_MAX_RETRIES", "3")
    try:
        value = int(raw)
    except ValueError:
        value = 3
    return max(1, value)


def _retry_delay_seconds(attempt: int) -> float:
    return min(60.0, 0.5 * (2**attempt))


def _should_retry(exc: BaseException) -> bool:
    status_code = getattr(exc, "status_code", None)
    return status_code in _RETRYABLE_STATUS_CODES


class OpenAIResponsesProvider:
    """Structured extraction provider using the OpenAI Responses API."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("FRE_MODEL_NAME", "gpt-4.1")

    def extract_json(self, *, prompt: str, schema: type[ModelT]) -> ModelT:
        """Return a validated Pydantic object from a structured model response."""
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ModelClientError(
                "The OpenAI SDK is not installed. Run `make setup-models` first."
            ) from exc

        max_retries = _max_retries()
        client = OpenAI()
        last_error: BaseException | None = None

        for attempt in range(max_retries):
            try:
                with log_model_call(model=self.model, schema_name=schema.__name__, prompt=prompt):
                    response = client.responses.parse(
                        model=self.model,
                        input=[
                            {
                                "role": "system",
                                "content": (
                                    "You extract source-grounded formalization-readiness artifacts. "
                                    "Return only data conforming to the supplied schema."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        text_format=schema,
                    )
                parsed = response.output_parsed
                if parsed is None:
                    raise ModelClientError("Structured model response did not contain parsed output.")
                return parsed
            except Exception as exc:
                last_error = exc
                if _should_retry(exc) and attempt < max_retries - 1:
                    time.sleep(_retry_delay_seconds(attempt))
                    continue
                break

        assert last_error is not None
        raise ModelClientError(f"OpenAI structured extraction failed: {last_error}") from last_error
