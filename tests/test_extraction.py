from fre_core.extraction import build_readiness_prompt, extract_readiness_report
from fre_core.schemas import ReadinessDimension, ReadinessReport, TheoremProofUnit


class FakeModelClient:
    def extract_json(self, *, prompt: str, schema: type[ReadinessReport]) -> ReadinessReport:
        assert "finite_tree_edge_count" in prompt
        return schema(
            unit_id="wrong_id_from_model",
            statement_readiness=ReadinessDimension(status="clear", recovered=["statement"], unresolved=[]),
            context_readiness=ReadinessDimension(status="partial", recovered=["tree"], unresolved=[]),
            notation_readiness=ReadinessDimension(status="partial", recovered=["|V|"], unresolved=["G-v"]),
            dependency_readiness=ReadinessDimension(status="partial", recovered=["induction"], unresolved=[]),
            existing_theorem_candidates=["SimpleGraph.IsTree.card_edgeFinset"],
            constructive_path=["leaf deletion"],
            blockers=["deletion notation"],
            recommended_next_action="Confirm existing theorem alignment.",
        )


def test_build_readiness_prompt_contains_source_material() -> None:
    unit = TheoremProofUnit(
        unit_id="finite_tree_edge_count",
        source_id="source",
        statement="Let G be a finite tree.",
        proof="Use induction.",
        domain="graph_theory",
    )

    prompt = build_readiness_prompt(unit)

    assert "finite_tree_edge_count" in prompt
    assert "Let G be a finite tree." in prompt
    assert "Use induction." in prompt


def test_extract_readiness_report_forces_unit_id_alignment() -> None:
    unit = TheoremProofUnit(
        unit_id="finite_tree_edge_count",
        source_id="source",
        statement="Let G be a finite tree.",
        proof="Use induction.",
        domain="graph_theory",
    )

    report = extract_readiness_report(unit=unit, model_client=FakeModelClient())

    assert report.unit_id == "finite_tree_edge_count"
    assert report.existing_theorem_candidates == ["SimpleGraph.IsTree.card_edgeFinset"]
