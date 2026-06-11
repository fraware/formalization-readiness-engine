import subprocess
from pathlib import Path

from fre_core import lean_runner
from fre_core.lean_runner import build_lean_check_command, check_lean_file


def test_build_lean_check_command() -> None:
    command = build_lean_check_command(Path("Example.lean"))

    assert command == ["lake", "env", "lean", "Example.lean"]


def test_check_lean_file_returns_result(monkeypatch) -> None:
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(lean_runner.subprocess, "run", fake_run)

    result = check_lean_file(path=Path("Example.lean"), cwd=Path("lean"))

    assert result.passed
    assert result.command == ["lake", "env", "lean", "Example.lean"]
    assert result.stdout == "ok"
