from types import SimpleNamespace

import pytest

from fre_core.model_client import ModelClientError
from fre_core.openai_responses_provider import OpenAIResponsesProvider
from fre_core.schemas import ReadinessDimension, ReadinessReport


class FakeAPIStatusError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"status {status_code}")
        self.status_code = status_code


class FakeResponses:
    def __init__(self, outcomes: list[object]) -> None:
        self._outcomes = outcomes
        self.calls = 0

    def parse(self, **kwargs: object) -> object:
        self.calls += 1
        outcome = self._outcomes[self.calls - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeOpenAI:
    def __init__(self, outcomes: list[object]) -> None:
        self.responses = FakeResponses(outcomes)


def _report() -> ReadinessReport:
    dimension = ReadinessDimension(status="clear", recovered=[], unresolved=[])
    return ReadinessReport(
        unit_id="u1",
        statement_readiness=dimension,
        context_readiness=dimension,
        notation_readiness=dimension,
        dependency_readiness=dimension,
        existing_theorem_candidates=[],
        constructive_path=[],
        blockers=[],
        recommended_next_action="next",
    )


def test_openai_provider_retries_on_429(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FRE_MAX_RETRIES", "3")
    parsed = _report()
    fake_client = FakeOpenAI(
        [
            FakeAPIStatusError(429),
            SimpleNamespace(output_parsed=parsed),
        ]
    )

    def fake_openai() -> FakeOpenAI:
        return fake_client

    monkeypatch.setattr("openai.OpenAI", fake_openai)
    provider = OpenAIResponsesProvider(model="fake-model")
    result = provider.extract_json(prompt="unit u1", schema=ReadinessReport)
    assert result.unit_id == "u1"
    assert fake_client.responses.calls == 2


def test_openai_provider_raises_after_exhausted_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FRE_MAX_RETRIES", "2")
    fake_client = FakeOpenAI([FakeAPIStatusError(500), FakeAPIStatusError(500)])

    def fake_openai() -> FakeOpenAI:
        return fake_client

    monkeypatch.setattr("openai.OpenAI", fake_openai)
    provider = OpenAIResponsesProvider(model="fake-model")
    with pytest.raises(ModelClientError):
        provider.extract_json(prompt="unit u1", schema=ReadinessReport)
    assert fake_client.responses.calls == 2
