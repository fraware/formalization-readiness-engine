"""OpenAI Responses provider for schema-constrained extraction."""

from __future__ import annotations

import os
from typing import TypeVar

from pydantic import BaseModel

from fre_core.model_client import ModelClientError

ModelT = TypeVar("ModelT", bound=BaseModel)


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

        client = OpenAI()
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
