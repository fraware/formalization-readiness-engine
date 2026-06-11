"""Render LeanTask packages into Lean source skeletons."""

from __future__ import annotations

import re
from pathlib import Path

from fre_core.schemas import LeanTaskLevel, LeanTaskPackage


def _safe_identifier(value: str) -> str:
    """Convert an arbitrary task identifier into a Lean-friendly identifier suffix."""
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    if not cleaned:
        return "generated_task"
    if cleaned[0].isdigit():
        return f"task_{cleaned}"
    return cleaned


def render_leantask(task: LeanTaskPackage) -> str:
    """Render a LeanTask package as a Lean source file.

    L0 tasks are rendered as documentation-only files. L1 and L2 tasks are
    rendered as executable skeletons when a formal target exists.
    """
    imports = task.imports or ["Mathlib"]
    lines: list[str] = []
    lines.extend(f"import {module}" for module in imports)
    lines.append("")
    lines.append("/-")
    lines.append(f"LeanTask: {task.leantask_id}")
    lines.append(f"Unit: {task.unit_id}")
    lines.append(f"Level: {task.level.value}")
    lines.append("")
    lines.append("Informal statement:")
    lines.append(task.informal_statement)
    lines.append("")
    lines.append("Next action:")
    lines.append(task.next_action)
    if task.proof_path:
        lines.append("")
        lines.append("Proof path:")
        lines.append(task.proof_path)
    if task.fallback_path:
        lines.append("")
        lines.append("Fallback path:")
        lines.append(task.fallback_path)
    lines.append("-/")
    lines.append("")

    if task.level == LeanTaskLevel.L0 or not task.formal_target:
        lines.append("-- L0 planning package. No Lean statement is emitted yet.")
        return "\n".join(lines) + "\n"

    identifier = _safe_identifier(task.leantask_id)
    hypotheses = " ".join(f"({hyp})" for hyp in task.hypotheses)
    if hypotheses:
        lines.append(f"theorem {identifier} {hypotheses} :")
    else:
        lines.append(f"theorem {identifier} :")
    lines.append(f"    {task.formal_target} := by")
    lines.append("  sorry")
    return "\n".join(lines) + "\n"


def write_leantask(task: LeanTaskPackage, output_path: Path) -> Path:
    """Write a LeanTask package to a Lean source file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_leantask(task), encoding="utf-8")
    return output_path
