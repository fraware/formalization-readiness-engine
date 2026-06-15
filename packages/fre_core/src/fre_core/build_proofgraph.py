"""ProofGraph builder from unit, readiness report, and alignment evidence."""

from __future__ import annotations

from fre_core.artifact_normalization import normalize_proofgraph
from fre_core.model_client import StructuredModelClient
from fre_core.schemas import AlignmentResult, ProofGraph, ReadinessReport, TheoremProofUnit
from fre_core.validation import PROOFGRAPH_EDGE_TYPES, validate_proofgraph

EDGE_LIST = ", ".join(sorted(PROOFGRAPH_EDGE_TYPES))


def build_proofgraph_prompt(
    unit: TheoremProofUnit,
    report: ReadinessReport | None = None,
    alignment: AlignmentResult | None = None,
) -> str:
    parts = [
        f"Build a proof graph. Allowed edge types: {EDGE_LIST}.",
        f"Unit: {unit.unit_id}",
        f"Statement: {unit.statement}",
        f"Proof: {unit.proof or ''}",
    ]
    if report is not None:
        parts.extend(
            [
                f"Blockers: {report.blockers}",
                f"Candidates: {report.existing_theorem_candidates}",
                f"Constructive path: {report.constructive_path}",
            ]
        )
    if alignment is not None:
        parts.append("Alignment: " + ", ".join(candidate.full_name for candidate in alignment.candidates[:10]))
    return "\n".join(parts)


def build_proofgraph(
    *,
    unit: TheoremProofUnit,
    model_client: StructuredModelClient,
    report: ReadinessReport | None = None,
    alignment: AlignmentResult | None = None,
) -> ProofGraph:
    graph = model_client.extract_json(
        prompt=build_proofgraph_prompt(unit, report, alignment),
        schema=ProofGraph,
    )
    if graph.unit_id != unit.unit_id:
        graph = graph.model_copy(update={"unit_id": unit.unit_id})
    graph = normalize_proofgraph(graph)
    validate_proofgraph(graph)
    validate_proofgraph(graph, mode="public_export")
    return graph
