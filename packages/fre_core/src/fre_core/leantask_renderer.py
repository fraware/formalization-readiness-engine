"""Render LeanTask packages into Lean source skeletons."""

from __future__ import annotations

import re
from pathlib import Path

from fre_core.schemas import LeanSubLemma, LeanTaskLevel, LeanTaskPackage


def _safe_identifier(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
    if not cleaned:
        return "generated_task"
    if cleaned[0].isdigit():
        return f"task_{cleaned}"
    return cleaned


def _render_hypothesis(hypothesis: str) -> str:
    stripped = hypothesis.strip()
    if not stripped:
        return ""
    if stripped.startswith("[") and stripped.endswith("]"):
        return stripped
    if stripped.startswith("(") and stripped.endswith(")"):
        return stripped
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    return f"({stripped})"


def _render_binder_list(hypotheses: list[str]) -> str:
    rendered = " ".join(
        item for item in (_render_hypothesis(hypothesis) for hypothesis in hypotheses) if item
    )
    return f" {rendered}" if rendered else ""


def _render_doc_header(task: LeanTaskPackage) -> list[str]:
    lines: list[str] = []
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
    if task.level == LeanTaskLevel.L2 and task.alignment_declarations:
        lines.append("")
        lines.append("Existing-theorem alignment report:")
        for declaration in task.alignment_declarations:
            lines.append(f"- {declaration}")
    lines.append("-/")
    lines.append("")
    return lines


def _render_sub_lemma(sub_lemma: LeanSubLemma) -> list[str]:
    identifier = _safe_identifier(sub_lemma.lemma_id)
    binders = _render_binder_list(sub_lemma.hypotheses)
    lines = [f"lemma {identifier}{binders} :"]
    lines.append(f"    {sub_lemma.statement} := by")
    lines.append("  sorry")
    lines.append("")
    return lines


def render_leantask(task: LeanTaskPackage) -> str:
    imports = task.imports or ["Mathlib"]
    lines: list[str] = []
    lines.extend(f"import {module}" for module in imports)
    if task.opens:
        lines.append("")
        lines.extend(f"open {namespace}" for namespace in task.opens)
    lines.append("")
    lines.extend(_render_doc_header(task))

    if task.level == LeanTaskLevel.L0 or not task.formal_target:
        lines.append("-- L0 planning package. No Lean statement is emitted yet.")
        return "\n".join(lines) + "\n"

    identifier = _safe_identifier(task.leantask_id)

    if task.level == LeanTaskLevel.L2:
        for sub_lemma in task.sub_lemmas:
            lines.extend(_render_sub_lemma(sub_lemma))

    binders = _render_binder_list(task.hypotheses)
    lines.append(f"theorem {identifier}{binders} :")
    lines.append(f"    {task.formal_target} := by")
    lines.append("  sorry")
    return "\n".join(lines) + "\n"


def write_leantask(task: LeanTaskPackage, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_leantask(task), encoding="utf-8")
    return output_path
