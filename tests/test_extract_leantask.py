"""Tests for LeanTask package extraction orchestration."""

import json
from pathlib import Path

import pytest

from fre_core.extract_leantask import (
    build_leantask_prompt,
    enrich_imports_from_index,
    extract_leantask_package,
)
from fre_core.mathlib_index import default_index_path, load_index
from fre_core.schemas import (
    LeanTaskLevel,
    LeanTaskPackage,
    ReadinessDimension,
    ReadinessReport,
    TheoremProofUnit,
)
from fre_core.validation import ArtifactValidationError, load_leantask_package


class FakeL0ModelClient:
    def extract_json(self, *, prompt: str, schema: type[LeanTaskPackage]) -> LeanTaskPackage:
        assert "finite_tree_edge_count" in prompt
        assert "Target LeanTask level: L0" in prompt
        assert "Existing theorem candidates:" in prompt
        return schema(
            leantask_id="wrong_leantask_id",
            unit_id="wrong_id_from_model",
            level=LeanTaskLevel.L0,
            informal_statement="Let G be a finite tree.",
            imports=["Mathlib.Combinatorics.SimpleGraph.Acyclic"],
            formal_target="G.edgeFinset.card + 1 = Fintype.card V",
            hypotheses=["[Fintype V]", "G : SimpleGraph V", "hG : G.IsTree"],
            proof_path="existing theorem alignment candidate",
            fallback_path="constructive decomposition into leaf-removal tasks",
            next_action="Confirm the exact mathlib theorem before promoting to L1.",
        )


class FakeL1ModelClient:
    def extract_json(self, *, prompt: str, schema: type[LeanTaskPackage]) -> LeanTaskPackage:
        assert "Target LeanTask level: L1" in prompt
        return schema(
            leantask_id="finite_tree_edge_count_L1",
            unit_id="finite_tree_edge_count",
            level=LeanTaskLevel.L1,
            informal_statement="Let G be a finite tree.",
            imports=["Mathlib.Combinatorics.SimpleGraph.Acyclic"],
            formal_target="G.edgeFinset.card + 1 = Fintype.card V",
            hypotheses=["[Fintype V]", "G : SimpleGraph V", "hG : G.IsTree"],
            proof_path="apply SimpleGraph.IsTree.card_edgeFinset",
            fallback_path="constructive leaf deletion",
            next_action="Typecheck this skeleton against the pinned lean/ Lake project.",
        )


class MissingFormalTargetL1ModelClient:
    def extract_json(self, *, prompt: str, schema: type[LeanTaskPackage]) -> LeanTaskPackage:
        return schema(
            leantask_id="finite_tree_edge_count_L1",
            unit_id="finite_tree_edge_count",
            level=LeanTaskLevel.L1,
            informal_statement="Let G be a finite tree.",
            imports=["Mathlib.Combinatorics.SimpleGraph.Acyclic"],
            formal_target=None,
            next_action="Add a formal target.",
        )


def _finite_tree_unit() -> TheoremProofUnit:
    return TheoremProofUnit(
        unit_id="finite_tree_edge_count",
        source_id="source",
        statement="Let G=(V,E) be a finite tree. Then |E| = |V| - 1.",
        proof="Use induction on |V|.",
        domain="graph_theory",
    )


def _finite_tree_report() -> ReadinessReport:
    return ReadinessReport(
        unit_id="finite_tree_edge_count",
        statement_readiness=ReadinessDimension(status="clear", recovered=["finite tree"], unresolved=[]),
        context_readiness=ReadinessDimension(status="partial", recovered=["graph"], unresolved=[]),
        notation_readiness=ReadinessDimension(status="partial", recovered=["|V|"], unresolved=["G-v"]),
        dependency_readiness=ReadinessDimension(status="partial", recovered=["induction"], unresolved=[]),
        existing_theorem_candidates=["SimpleGraph.IsTree.card_edgeFinset"],
        constructive_path=["leaf deletion"],
        blockers=["deletion notation"],
        recommended_next_action="Confirm existing theorem alignment.",
    )


def test_build_leantask_prompt_contains_source_and_report() -> None:
    unit = _finite_tree_unit()
    report = _finite_tree_report()

    prompt = build_leantask_prompt(unit=unit, report=report, level=LeanTaskLevel.L0)

    assert "finite_tree_edge_count" in prompt
    assert "Let G=(V,E) be a finite tree." in prompt
    assert "SimpleGraph.IsTree.card_edgeFinset" in prompt
    assert "Target LeanTask level: L0" in prompt
    assert "existing-theorem alignment" in prompt


def test_extract_leantask_package_forces_unit_id_alignment() -> None:
    package = extract_leantask_package(
        unit=_finite_tree_unit(),
        report=_finite_tree_report(),
        model_client=FakeL0ModelClient(),
    )

    assert package.unit_id == "finite_tree_edge_count"
    assert package.level == LeanTaskLevel.L0
    assert package.next_action.startswith("Confirm the exact mathlib")


def test_extract_leantask_package_l1_requires_formal_target() -> None:
    package = extract_leantask_package(
        unit=_finite_tree_unit(),
        report=_finite_tree_report(),
        model_client=FakeL1ModelClient(),
        level=LeanTaskLevel.L1,
    )

    assert package.level == LeanTaskLevel.L1
    assert package.formal_target == "G.edgeFinset.card + 1 = Fintype.card V"


def test_extract_leantask_package_rejects_l1_without_formal_target() -> None:
    with pytest.raises(ArtifactValidationError) as excinfo:
        extract_leantask_package(
            unit=_finite_tree_unit(),
            report=_finite_tree_report(),
            model_client=MissingFormalTargetL1ModelClient(),
            level=LeanTaskLevel.L1,
        )

    assert "missing_formal_target" in str(excinfo.value)


def test_enrich_imports_from_index_is_deterministic() -> None:
    report = _finite_tree_report()
    index = load_index(default_index_path())

    imports = enrich_imports_from_index(report=report, index=index, top_k=3)

    assert imports
    assert len(imports) == len(set(imports))


def test_extract_leantask_package_can_enrich_imports() -> None:
    index = load_index(default_index_path())
    package = extract_leantask_package(
        unit=_finite_tree_unit(),
        report=_finite_tree_report(),
        model_client=FakeL0ModelClient(),
        enrich_imports=True,
        index=index,
    )

    assert len(package.imports) >= 2


def test_generated_l0_structure_matches_finite_tree_gold() -> None:
    package = extract_leantask_package(
        unit=_finite_tree_unit(),
        report=_finite_tree_report(),
        model_client=FakeL0ModelClient(),
    )
    gold = load_leantask_package(Path("examples/finite_tree/leantask.json"))

    assert package.level == gold.level
    assert package.unit_id == gold.unit_id
    assert package.informal_statement
    assert package.imports
    assert package.next_action
    assert package.proof_path
    assert package.fallback_path
    assert "alignment" in (package.proof_path or "").lower() or "theorem" in (package.proof_path or "").lower()

    gold_payload = json.loads(Path("examples/finite_tree/leantask.json").read_text(encoding="utf-8"))
    generated_payload = json.loads(package.model_dump_json())
    for field in ("level", "unit_id", "schema_version"):
        assert generated_payload[field] == gold_payload[field]
