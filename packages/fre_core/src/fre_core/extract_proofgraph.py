"""ProofGraph extraction orchestration.

This module converts a theorem/proof unit into structured proof-graph evidence using
an injected structured model client. It does not import provider SDKs directly.
"""

from __future__ import annotations

from fre_core.model_client import StructuredModelClient
from fre_core.schemas import ProofGraph, TheoremProofUnit
from fre_core.validation import validate_proofgraph


PROOFGRAPH_EXTRACTION_INSTRUCTIONS = """
You are extracting a source-grounded proof graph for formalization readiness.

Follow these rules:
1. Create nodes for the theorem statement, assumptions, proof strategy, blockers, and library candidates.
2. Connect nodes with edges that reflect how the proof uses assumptions, aligns with library theorems, or is blocked.
3. Keep node text concise and grounded in the supplied source material.
4. Every edge source and target must refer to a node_id present in the nodes list.
5. Do not invent formal theorem names unless they are presented as library candidates.
""".strip()


def build_proofgraph_prompt(unit: TheoremProofUnit) -> str:
    """Build the prompt for proof-graph extraction from one theorem/proof unit."""
    proof = unit.proof or "No proof body was provided."
    context = unit.local_context or "No local context was provided."

    return f"""
{PROOFGRAPH_EXTRACTION_INSTRUCTIONS}

Unit identifier: {unit.unit_id}
Domain: {unit.domain}

Local context:
{context}

Theorem statement:
{unit.statement}

Proof body:
{proof}
""".strip()


def extract_proofgraph(
    *,
    unit: TheoremProofUnit,
    model_client: StructuredModelClient,
) -> ProofGraph:
    """Extract a proof graph for one theorem/proof unit."""
    prompt = build_proofgraph_prompt(unit)
    graph = model_client.extract_json(prompt=prompt, schema=ProofGraph)
    if graph.unit_id != unit.unit_id:
        graph = graph.model_copy(update={"unit_id": unit.unit_id})
    validate_proofgraph(graph)
    return graph
