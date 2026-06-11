"""Tests for Atlas record extraction orchestration."""

import pytest

from fre_core.extract_atlas import build_atlas_prompt, extract_atlas_record
from fre_core.schemas import AtlasRecord, TheoremProofUnit
from fre_core.validation import ArtifactValidationError


class FakeAtlasModelClient:
    def extract_json(self, *, prompt: str, schema: type[AtlasRecord]) -> AtlasRecord:
        assert "finite_tree_edge_count" in prompt
        return schema(
            unit_id="wrong_id_from_model",
            blocker_type="notation_alignment",
            mathematical_pattern="finite-tree induction over a removed vertex",
            evidence="let G prime be G with v removed",
            candidate_formal_object="induced subgraph on the remaining vertices",
            likely_library_location="Mathlib.Combinatorics.SimpleGraph",
            severity="high",
            status="candidate",
            recommended_action="Align the informal vertex-removal step before constructive proof decomposition.",
        )


class MissingEvidenceAtlasModelClient:
    def extract_json(self, *, prompt: str, schema: type[AtlasRecord]) -> AtlasRecord:
        return schema(
            unit_id="finite_tree_edge_count",
            blocker_type="notation_alignment",
            mathematical_pattern="finite-tree induction",
            evidence="   ",
            severity="high",
            status="candidate",
            recommended_action="Fix notation.",
        )


def _finite_tree_unit() -> TheoremProofUnit:
    return TheoremProofUnit(
        unit_id="finite_tree_edge_count",
        source_id="source",
        statement="Let G be a finite tree.",
        proof="Use induction.",
        domain="graph_theory",
    )


def test_build_atlas_prompt_contains_source_material() -> None:
    unit = _finite_tree_unit()

    prompt = build_atlas_prompt(unit)

    assert "finite_tree_edge_count" in prompt
    assert "Let G be a finite tree." in prompt
    assert "Use induction." in prompt
    assert "Atlas" in prompt


def test_extract_atlas_record_forces_unit_id_alignment() -> None:
    record = extract_atlas_record(unit=_finite_tree_unit(), model_client=FakeAtlasModelClient())

    assert record.unit_id == "finite_tree_edge_count"
    assert record.evidence == "let G prime be G with v removed"
    assert record.recommended_action.startswith("Align the informal")


def test_extract_atlas_record_rejects_missing_evidence() -> None:
    with pytest.raises(ArtifactValidationError) as excinfo:
        extract_atlas_record(unit=_finite_tree_unit(), model_client=MissingEvidenceAtlasModelClient())

    assert "missing_evidence" in str(excinfo.value)
