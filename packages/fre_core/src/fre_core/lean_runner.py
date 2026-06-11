"""Lean checking utilities for rendered LeanTask files."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LeanCheckResult:
    """Result of checking one Lean file."""

    path: Path
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


def build_lean_check_command(path: Path) -> list[str]:
    """Build the command used to check a single Lean file."""
    return ["lake", "env", "lean", str(path)]


def check_lean_file(*, path: Path, cwd: Path | None = None, timeout_seconds: int = 60) -> LeanCheckResult:
    """Run Lean on a single file through Lake.

    The caller is responsible for ensuring the selected working directory contains
    the intended Lake project.
    """
    command = build_lean_check_command(path)
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    return LeanCheckResult(
        path=path,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
