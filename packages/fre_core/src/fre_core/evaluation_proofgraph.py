"""Deterministic ProofGraph evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from fre_core.evaluation import PrecisionRecallF1, score_label_set
from fre_core.schemas import ProofGraph, ProofGraphEdge, ProofGraphNode


def _node_key(node: ProofGraphNode) -> str:
    return f"{node.node_type.casefold()}::{' '.join(node.text.casefold().split())}"


def _edge_key(edge: ProofGraphEdge) -> str:
    return f"{edge.source.casefold()}->{edge.target.casefold()}::{edge.edge_type.casefold()}"


@dataclass(frozen=True)
class ProofGraphScores:
    nodes: PrecisionRecallF1
    edges: PrecisionRecallF1

    @property
    def macro_f1(self) -> float:
        return (self.nodes.f1 + self.edges.f1) / 2


def score_proofgraph(*, predicted: ProofGraph, gold: ProofGraph) -> ProofGraphScores:
    if predicted.unit_id != gold.unit_id:
        raise ValueError(f"Unit mismatch: predicted={predicted.unit_id!r}, gold={gold.unit_id!r}")
    return ProofGraphScores(
        nodes=score_label_set(
            predicted=[_node_key(node) for node in predicted.nodes],
            gold=[_node_key(node) for node in gold.nodes],
        ),
        edges=score_label_set(
            predicted=[_edge_key(edge) for edge in predicted.edges],
            gold=[_edge_key(edge) for edge in gold.edges],
        ),
    )
