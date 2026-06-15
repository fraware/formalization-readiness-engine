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


def build_readiness_prompt(
    unit: TheoremProofUnit,
    *,
    suggested_declarations: list[str] | None = None,
) -> str:
    """Build the prompt for readiness extraction from one theorem/proof unit."""
    proof = unit.proof or "No proof body was provided."
    context = unit.local_context or "No local context was provided."

    suggestions_block = ""
    if suggested_declarations:
        formatted = "\n".join(f"- {name}" for name in suggested_declarations)
        suggestions_block = f"""
Suggested mathlib declarations from index (ranked):
{formatted}

Choose from these declarations when appropriate, or emit none if none apply.
"""

    return f"""
{READINESS_EXTRACTION_INSTRUCTIONS}
{suggestions_block}
Unit identifier: {unit.unit_id}
Domain: {unit.domain}

Local context:
{context}

Theorem statement:
{unit.statement}

Proof body:
{proof}
""".strip()


def _merge_theorem_candidates(
    model_candidates: list[str],
    index_candidates: list[str],
) -> list[str]:
    """Union model and index candidates, preferring index full_names on near-misses."""
    index_by_key = {_normalize_theorem_candidate(name).casefold(): name for name in index_candidates}
    merged: list[str] = []
    seen: set[str] = set()

    def add(candidate: str) -> None:
        normalized = _normalize_theorem_candidate(candidate)
        if not normalized:
            return
        key = normalized.casefold()
        if key in seen:
            return
        canonical = index_by_key.get(key, normalized)
        seen.add(canonical.casefold())
        merged.append(canonical)

    for candidate in model_candidates:
        add(candidate)
    for candidate in index_candidates:
        add(candidate)
    return merged


def extract_readiness_report(
    *,
    unit: TheoremProofUnit,
    model_client: StructuredModelClient,
    enrich_candidates: bool = False,
    index: DeclarationIndex | None = None,
    candidate_top_k: int = 5,
    use_index_suggestions: bool = False,
) -> ReadinessReport:
    """Extract a readiness report for one theorem/proof unit.

    When ``enrich_candidates`` is True, ``existing_theorem_candidates`` are replaced
    with deterministic index lookup results. Requires a loaded ``DeclarationIndex``.

    When ``use_index_suggestions`` is True, ranked index declarations are injected
    into the extraction prompt and merged with model output afterward.
    """
    index_suggestions: list[str] = []
    if use_index_suggestions:
        if index is None:
            raise ValueError("use_index_suggestions requires a DeclarationIndex")
        from fre_core.mathlib_index import suggest_declarations_for_unit

        index_suggestions = suggest_declarations_for_unit(
            unit=unit,
            index=index,
            top_k=candidate_top_k,
        )

    prompt = build_readiness_prompt(unit, suggested_declarations=index_suggestions or None)
    report = model_client.extract_json(prompt=prompt, schema=ReadinessReport)
    report = _normalize_readiness_report(report)
    if report.unit_id != unit.unit_id:
        report = report.model_copy(update={"unit_id": unit.unit_id})
    if use_index_suggestions and index_suggestions:
        merged = _merge_theorem_candidates(report.existing_theorem_candidates, index_suggestions)
        report = report.model_copy(update={"existing_theorem_candidates": merged})
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
