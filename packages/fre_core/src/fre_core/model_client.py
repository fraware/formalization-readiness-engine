"""Central interface for structured model calls.

Extraction code should depend on this interface rather than importing a provider
SDK directly. Provider implementations can live behind this boundary.
"""

from __future__ import annotations

import json
from typing import Protocol, TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class StructuredModelClient(Protocol):
    """Protocol for schema-constrained model extraction."""

    def extract_json(self, *, prompt: str, schema: type[ModelT]) -> ModelT:
        """Return a validated Pydantic object from a model response."""


class ModelClientError(RuntimeError):
    """Raised when a model call fails or returns invalid structured output."""


def parse_json_as_schema(raw: str, schema: type[ModelT]) -> ModelT:
    """Validate a raw JSON string against a Pydantic schema."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ModelClientError(f"Model output was not valid JSON: {exc}") from exc
    return schema.model_validate(payload)
