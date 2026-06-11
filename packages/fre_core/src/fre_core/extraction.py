"""Readiness extraction orchestration.

This module converts a theorem/proof unit into a structured readiness report using
an injected structured model client. It does not import provider SDKs directly.
"""

from __future__ import annotations

from fre_core.model_client import StructuredModelClient
from fre_core.schemas import ReadinessReport, TheoremProofUnit


READINESS_EXTRACTION_INSTRUCTIONS = """
You are extracting a source-grounded formalization-readiness report.

Follow these rules:
1. Preserve the distinction between an existing-theorem alignment path and a constructive proof path.
2. Report unresolved notation, missing assumptions, missing prerequisites, and library-alignment blockers.
3. Do not invent formal theorem names unless they are presented as candidates.
4. Keep every field concise and actionable.
5. The recommended next action must be specific enough for a formalizer to act on.
""".strip()


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
) -> ReadinessReport:
    """Extract a readiness report for one theorem/proof unit."""
    prompt = build_readiness_prompt(unit)
    report = model_client.extract_json(prompt=prompt, schema=ReadinessReport)
    if report.unit_id != unit.unit_id:
        report = report.model_copy(update={"unit_id": unit.unit_id})
    return report
