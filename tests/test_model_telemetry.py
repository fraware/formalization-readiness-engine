import logging

from fre_core.model_telemetry import hash_prompt, log_model_call


def test_hash_prompt_is_deterministic() -> None:
    first = hash_prompt("prompt text")
    second = hash_prompt("prompt text")
    assert first == second


def test_hash_prompt_is_stable() -> None:
    digest = hash_prompt("prompt text")
    assert len(digest) == 16


def test_log_model_call_context_manager_runs() -> None:
    with log_model_call(model="fake", schema_name="ReadinessReport", prompt="hello"):
        pass


def test_log_model_call_emits_start_and_end(caplog) -> None:
    caplog.set_level(logging.INFO, logger="fre_core.model_telemetry")
    with log_model_call(model="fake", schema_name="ReadinessReport", prompt="hello"):
        pass
    assert "model_call_start" in caplog.text
    assert "model_call_end" in caplog.text
