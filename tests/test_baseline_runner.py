from pathlib import Path

from fre_core.baseline_runner import BaselineCondition, load_baseline_units, run_baselines
from fre_core.schemas import (
    AtlasRecord,
    LeanTaskLevel,
    LeanTaskPackage,
    ProofGraph,
    ProofGraphNode,
    ReadinessDimension,
    ReadinessReport,
)


class FakeModelClient:
    """Deterministic model client for baseline harness tests."""

    model = "fake-model"

    def extract_json(self, *, prompt: str, schema: type[object]) -> object:
        unit_id = "finite_tree_edge_count"
        if "category_theory_pullback_equivalence" in prompt:
            unit_id = "category_theory_pullback_equivalence"

        dimension = ReadinessDimension(status="clear", recovered=[], unresolved=[])
        if schema is ReadinessReport:
            return ReadinessReport(
                unit_id=unit_id,
                statement_readiness=dimension,
                context_readiness=dimension,
                notation_readiness=dimension,
                dependency_readiness=dimension,
                existing_theorem_candidates=["SimpleGraph.IsTree.card_edgeFinset"],
                constructive_path=["leaf deletion"],
                blockers=["notation mismatch"],
                recommended_next_action="Confirm alignment.",
            )
        if schema is ProofGraph:
            return ProofGraph(
                unit_id=unit_id,
                nodes=[
                    ProofGraphNode(
                        node_id="N1",
                        node_type="theorem_statement",
                        text="statement",
                    )
                ],
                edges=[],
            )
        if schema is AtlasRecord:
            return AtlasRecord(
                unit_id=unit_id,
                blocker_type="notation_alignment",
                mathematical_pattern="pattern",
                evidence="evidence",
                severity="high",
                status="candidate",
                recommended_action="Align notation.",
            )
        if schema is LeanTaskPackage:
            return LeanTaskPackage(
                leantask_id=f"{unit_id}_L0",
                unit_id=unit_id,
                level=LeanTaskLevel.L0,
                informal_statement="statement",
                imports=["Mathlib.Combinatorics.SimpleGraph.Acyclic"],
                formal_target="target",
                hypotheses=["h"],
                next_action="Next.",
            )
        raise AssertionError(f"Unexpected schema: {schema!r}")


def test_run_baselines_writes_artifacts_for_each_condition(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = repo_root / "benchmarks" / "baselines" / "manifest.json"
    units = load_baseline_units(repo_root=repo_root, manifest_path=manifest_path)
    assert len(units) == 2

    result = run_baselines(
        output_dir=tmp_path,
        model_client=FakeModelClient(),
        repo_root=repo_root,
        manifest_path=manifest_path,
        run_id="test_run",
        conditions=(BaselineCondition.DIRECT, BaselineCondition.WITH_ALIGNMENT),
        model_name="fake-model",
    )

    assert result.unit_count == 2
    assert result.condition_count == 2
    assert (result.output_dir / "run_manifest.json").is_file()

    direct_unit = result.output_dir / BaselineCondition.DIRECT.value / "finite_tree_edge_count"
    assert (direct_unit / "readiness_report.json").is_file()
    assert (direct_unit / "proofgraph.json").is_file()
    assert (direct_unit / "atlas_record.json").is_file()
    assert (direct_unit / "leantask.json").is_file()
    assert not (direct_unit / "alignment.json").exists()

    aligned_unit = (
        result.output_dir / BaselineCondition.WITH_ALIGNMENT.value / "finite_tree_edge_count"
    )
    assert (aligned_unit / "alignment.json").is_file()
