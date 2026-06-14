from pathlib import Path

import subprocess

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


def test_generated_finite_tree_lean_file_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    generated = root / "lean" / "FRETasks" / "Generated" / "FiniteTree.lean"
    assert generated.is_file()
    assert "finite_tree_edge_count_L1" in generated.read_text(encoding="utf-8")


def test_generated_category_theory_lean_file_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    generated = root / "lean" / "FRETasks" / "Generated" / "CategoryTheoryPullback.lean"
    assert generated.is_file()
    assert "category_theory_pullback_equivalence_L1" in generated.read_text(encoding="utf-8")
