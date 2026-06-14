"""ProofGraph extraction orchestration."""
from __future__ import annotations
from fre_core.build_proofgraph import build_proofgraph, build_proofgraph_prompt
from fre_core.model_client import StructuredModelClient
from fre_core.schemas import AlignmentResult, ProofGraph, ReadinessReport, TheoremProofUnit

def extract_proofgraph(*, unit: TheoremProofUnit, model_client: StructuredModelClient, report: ReadinessReport | None = None, alignment: AlignmentResult | None = None, from_unit_only: bool = False) -> ProofGraph:
    if from_unit_only:
        report, alignment = None, None
    return build_proofgraph(unit=unit, model_client=model_client, report=report, alignment=alignment)

__all__ = ["build_proofgraph_prompt", "extract_proofgraph"]
