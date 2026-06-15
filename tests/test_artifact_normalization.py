from pathlib import Path

import pytest

from fre_core.artifact_normalization import normalize_atlas_record, normalize_proofgraph
from fre_core.schemas import AtlasRecord, ProofGraph, ProofGraphNode
from fre_core.validation import load_atlas_record, load_proofgraph

ROOT = Path(__file__).resolve().parents[1]
LIVE_ROOT = ROOT / "artifacts" / "generated" / "demo_run" / "live"


@pytest.mark.parametrize(
    ("example_key", "filename", "loader", "normalizer"),
    [
        ("finite_tree", "proofgraph.model.json", load_proofgraph, normalize_proofgraph),
        ("category_theory_pullback", "proofgraph.model.json", load_proofgraph, normalize_proofgraph),
        ("finite_tree", "atlas_record.model.json", load_atlas_record, normalize_atlas_record),
        ("category_theory_pullback", "atlas_record.model.json", load_atlas_record, normalize_atlas_record),
    ],
)
def test_live_artifacts_pass_public_export_after_normalization(
    example_key: str,
    filename: str,
    loader,
    normalizer,
) -> None:
    path = LIVE_ROOT / example_key / filename
    if not path.is_file():
        pytest.skip(f"live artifact missing: {path}")

    artifact = loader(path, mode="permissive")
    normalized = normalizer(artifact)
    if isinstance(normalized, ProofGraph):
        from fre_core.validation import validate_proofgraph

        validate_proofgraph(normalized, mode="public_export")
    else:
        from fre_core.validation import validate_atlas_record

        validate_atlas_record(normalized, mode="public_export")


def test_normalize_proofgraph_preserves_raw_node_type() -> None:
    graph = ProofGraph(
        unit_id="u1",
        nodes=[
            ProofGraphNode(node_id="n1", node_type="theorem", text="statement"),
            ProofGraphNode(node_id="n2", node_type="base_case", text="base"),
        ],
        edges=[],
    )
    normalized = normalize_proofgraph(graph)
    assert normalized.nodes[0].node_type == "theorem_statement"
    assert normalized.nodes[0].raw_node_type == "theorem"
    assert normalized.nodes[1].node_type == "proof_step"
    assert normalized.nodes[1].raw_node_type == "base_case"


def test_normalize_atlas_record_maps_definition_gap() -> None:
    record = AtlasRecord(
        unit_id="u1",
        blocker_type="definition-gap",
        mathematical_pattern="pattern",
        evidence="source quote",
        severity="medium",
        status="open",
        recommended_action="align definitions",
    )
    normalized = normalize_atlas_record(record)
    assert normalized.blocker_type == "notation_alignment"
    assert normalized.blocker_type_raw == "definition-gap"
