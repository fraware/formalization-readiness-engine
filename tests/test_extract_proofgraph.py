"""Tests for ProofGraph extraction orchestration."""

import pytest

from fre_core.extract_proofgraph import build_proofgraph_prompt, extract_proofgraph
from fre_core.schemas import ProofGraph, TheoremProofUnit
from fre_core.validation import ArtifactValidationError


class FakeProofGraphModelClient:
    def extract_json(self, *, prompt: str, schema: type[ProofGraph]) -> ProofGraph:
        assert "finite_tree_edge_count" in prompt
        return schema(
            unit_id="wrong_id_from_model",
            nodes=[
                {"node_id": "N_statement", "node_type": "theorem_statement", "text": "Let G be a finite tree."},
                {"node_id": "N_tree_assumption", "node_type": "assumption", "text": "G is a finite tree."},
            ],
            edges=[{"source": "N_statement", "target": "N_tree_assumption", "edge_type": "uses_assumption"}],
        )


class BrokenEdgeProofGraphModelClient:
    def extract_json(self, *, prompt: str, schema: type[ProofGraph]) -> ProofGraph:
        return schema(
            unit_id="finite_tree_edge_count",
            nodes=[{"node_id": "N1", "node_type": "statement", "text": "A theorem."}],
            edges=[{"source": "N1", "target": "N_missing", "edge_type": "uses"}],
        )


def _finite_tree_unit() -> TheoremProofUnit:
    return TheoremProofUnit(
        unit_id="finite_tree_edge_count",
        source_id="source",
        statement="Let G be a finite tree.",
        proof="Use induction.",
        domain="graph_theory",
    )


def test_build_proofgraph_prompt_contains_source_material() -> None:
    unit = _finite_tree_unit()

    prompt = build_proofgraph_prompt(unit)

    assert "finite_tree_edge_count" in prompt
    assert "Let G be a finite tree." in prompt
    assert "Use induction." in prompt
    assert "proof graph" in prompt.lower()


def test_extract_proofgraph_forces_unit_id_alignment() -> None:
    graph = extract_proofgraph(unit=_finite_tree_unit(), model_client=FakeProofGraphModelClient())

    assert graph.unit_id == "finite_tree_edge_count"
    assert len(graph.nodes) == 2
    assert graph.edges[0].target == "N_tree_assumption"


def test_extract_proofgraph_rejects_broken_edges() -> None:
    with pytest.raises(ArtifactValidationError) as excinfo:
        extract_proofgraph(unit=_finite_tree_unit(), model_client=BrokenEdgeProofGraphModelClient())

    assert "missing_edge_target" in str(excinfo.value)
