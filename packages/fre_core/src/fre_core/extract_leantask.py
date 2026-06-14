"""LeanTask package extraction orchestration.

This module converts a theorem/proof unit and readiness report into a LeanTask package
using an injected structured model client. It does not import provider SDKs directly.
"""

from __future__ import annotations

from fre_core.mathlib_index import build_search_query_from_report, search
from fre_core.model_client import StructuredModelClient
from fre_core.schemas import DeclarationIndex, LeanTaskLevel, LeanTaskPackage, ReadinessReport, TheoremProofUnit
from fre_core.validation import validate_leantask_package


LEANTASK_GENERATION_INSTRUCTIONS = """
You are generating a source-grounded LeanTask package for formalization readiness.

Follow these rules:
1. Default to L0: a planning package with informal statement, blockers, candidate imports, proof paths, and next action.
2. Use L1 only when existing-theorem alignment is strong: emit a typechecked Lean theorem statement skeleton with imports, hypotheses, formal_target, and sorry placeholders implied by the level.
3. Preserve the distinction between an existing-theorem alignment path and a constructive proof path in proof_path and fallback_path.
4. Do not invent confirmed mathlib theorem names; present alignment candidates only.
5. Keep imports as mathlib module paths (for example Mathlib.Combinatorics.SimpleGraph.Acyclic).
6. The next_action must be specific enough for a formalizer to act on.
7. Set leantask_id to a stable identifier derived from the unit_id and level.
""".strip()


def _format_readiness_report(report: ReadinessReport) -> str:
    return f"""
Statement readiness: {report.statement_readiness.status}
  recovered: {", ".join(report.statement_readiness.recovered) or "(none)"}
  unresolved: {", ".join(report.statement_readiness.unresolved) or "(none)"}

Context readiness: {report.context_readiness.status}
  recovered: {", ".join(report.context_readiness.recovered) or "(none)"}
  unresolved: {", ".join(report.context_readiness.unresolved) or "(none)"}

Notation readiness: {report.notation_readiness.status}
  recovered: {", ".join(report.notation_readiness.recovered) or "(none)"}
  unresolved: {", ".join(report.notation_readiness.unresolved) or "(none)"}

Dependency readiness: {report.dependency_readiness.status}
  recovered: {", ".join(report.dependency_readiness.recovered) or "(none)"}
  unresolved: {", ".join(report.dependency_readiness.unresolved) or "(none)"}

Existing theorem candidates: {", ".join(report.existing_theorem_candidates) or "(none)"}
Constructive path: {", ".join(report.constructive_path) or "(none)"}
Blockers: {", ".join(report.blockers) or "(none)"}
Recommended next action: {report.recommended_next_action}
""".strip()


def build_leantask_prompt(
    *,
    unit: TheoremProofUnit,
    report: ReadinessReport,
    level: LeanTaskLevel,
) -> str:
    """Build the prompt for LeanTask generation from one unit and readiness report."""
    proof = unit.proof or "No proof body was provided."
    context = unit.local_context or "No local context was provided."

    return f"""
{LEANTASK_GENERATION_INSTRUCTIONS}

Target LeanTask level: {level.value}

Unit identifier: {unit.unit_id}
Domain: {unit.domain}

Local context:
{context}

Theorem statement:
{unit.statement}

Proof body:
{proof}

Readiness report:
{_format_readiness_report(report)}
""".strip()


def enrich_imports_from_index(
    *,
    report: ReadinessReport,
    index: DeclarationIndex,
    top_k: int = 5,
) -> list[str]:
    """Suggest mathlib module imports from deterministic index lookup on the report."""
    query = build_search_query_from_report(report)
    hits = search(index=index, query=query, top_k=top_k)
    seen: set[str] = set()
    imports: list[str] = []
    for hit in hits:
        module = hit.declaration.module
        if module not in seen:
            seen.add(module)
            imports.append(module)
    return imports


def extract_leantask_package(
    *,
    unit: TheoremProofUnit,
    report: ReadinessReport,
    model_client: StructuredModelClient,
    level: LeanTaskLevel = LeanTaskLevel.L0,
    enrich_imports: bool = False,
    index: DeclarationIndex | None = None,
    import_top_k: int = 5,
) -> LeanTaskPackage:
    """Extract a LeanTask package for one theorem/proof unit and readiness report."""
    if report.unit_id != unit.unit_id:
        raise ValueError(
            f"Readiness report unit_id {report.unit_id!r} does not match unit {unit.unit_id!r}"
        )

    prompt = build_leantask_prompt(unit=unit, report=report, level=level)
    package = model_client.extract_json(prompt=prompt, schema=LeanTaskPackage)

    updates: dict[str, object] = {}
    if package.unit_id != unit.unit_id:
        updates["unit_id"] = unit.unit_id
    if package.level != level:
        updates["level"] = level
    if updates:
        package = package.model_copy(update=updates)

    if enrich_imports:
        if index is None:
            raise ValueError("enrich_imports requires a DeclarationIndex")
        suggested = enrich_imports_from_index(report=report, index=index, top_k=import_top_k)
        merged = list(dict.fromkeys([*package.imports, *suggested]))
        package = package.model_copy(update={"imports": merged})

    validate_leantask_package(package)
    return package
