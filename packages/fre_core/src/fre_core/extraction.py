"""Readiness extraction orchestration.

This module converts a theorem/proof unit into a structured readiness report using
an injected structured model client. It does not import provider SDKs directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fre_core.model_client import StructuredModelClient
from fre_core.schemas import ReadinessReport, TheoremProofUnit

if TYPE_CHECKING:
    from fre_core.schemas import DeclarationIndex


READINESS_EXTRACTION_INSTRUCTIONS = """
You are extracting a source-grounded formalization-readiness report.

Follow these rules:
1. Preserve the distinction between an existing-theorem alignment path and a constructive proof path.
2. Report unresolved notation, missing assumptions, missing prerequisites, and library-alignment blockers.
3. Do not invent formal theorem names unless they are presented as candidates.
4. Keep every field concise and actionable.
5. The recommended next action must be specific enough for a formalizer to act on.
6. For existing_theorem_candidates, emit Lean/mathlib declaration full names only (dot-separated, e.g. SimpleGraph.IsTree.card_edgeFinset). Do not use mathlib: prefixes, Coq/Isabelle names, or other ecosystems.
7. Use readiness dimension status values clear, partial, blocked, or pending (not ready or partially_ready).
""".strip()


def _normalize_theorem_candidate(value: str) -> str:
    """Normalize model-emitted theorem candidates to mathlib full_name form."""
    stripped = value.strip()
    if stripped.casefold().startswith("mathlib:"):
        return stripped.split(":", 1)[1].strip()
    return stripped


def _normalize_readiness_report(report: ReadinessReport) -> ReadinessReport:
    """Apply deterministic post-processing to model extraction output."""
    candidates = [_normalize_theorem_candidate(item) for item in report.existing_theorem_candidates]
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        key = candidate.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    if deduped == report.existing_theorem_candidates:
        return report
    return report.model_copy(update={"existing_theorem_candidates": deduped})


def build_readiness_prompt(unit: TheoremProofUnit) -> str:
    """Build the prompt for readiness extraction from one theorem/proof unit."""
    proof = unit.proof or "No proof body was provided."
    context = unit.local_context or "No local context was provided."

    return f"""
{READINESS_EXTRACTION_INSTRUCTIONS}

Unit identifier: {unit.unit_id}
Domain: {unit.domain}

Local context:
{context}

Theorem statement:
{unit.statement}

Proof body:
{proof}
""".strip()


def extract_readiness_report(
    *,
    unit: TheoremProofUnit,
    model_client: StructuredModelClient,
    enrich_candidates: bool = False,
    index: DeclarationIndex | None = None,
    candidate_top_k: int = 5,
) -> ReadinessReport:
    """Extract a readiness report for one theorem/proof unit.

    When ``enrich_candidates`` is True, ``existing_theorem_candidates`` are replaced
    with deterministic index lookup results. Requires a loaded ``DeclarationIndex``.
    """
    prompt = build_readiness_prompt(unit)
    report = model_client.extract_json(prompt=prompt, schema=ReadinessReport)
    report = _normalize_readiness_report(report)
    if report.unit_id != unit.unit_id:
        report = report.model_copy(update={"unit_id": unit.unit_id})
    if enrich_candidates:
        if index is None:
            raise ValueError("enrich_candidates requires a DeclarationIndex")
        from fre_core.mathlib_index import enrich_readiness_report_from_unit

        report = enrich_readiness_report_from_unit(
            report=report,
            unit=unit,
            index=index,
            top_k=candidate_top_k,
        )
    return report
