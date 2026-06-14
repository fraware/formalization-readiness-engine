import pytest

from fre_core.leantask_renderer import render_leantask
from fre_core.schemas import LeanSubLemma, LeanTaskLevel, LeanTaskPackage
from fre_core.validation import ArtifactValidationError, load_leantask_package, validate_leantask_package


def test_render_l0_leantask_as_documentation_only_file() -> None:
    task = LeanTaskPackage(
        leantask_id="finite_tree_edge_count_L0",
        unit_id="finite_tree_edge_count",
        level=LeanTaskLevel.L0,
        informal_statement="Let G be a finite tree.",
        next_action="Confirm alignment before statement generation.",
    )

    rendered = render_leantask(task)

    assert "LeanTask: finite_tree_edge_count_L0" in rendered
    assert "L0 planning package" in rendered
    assert "theorem" not in rendered


def test_render_l1_leantask_as_lean_skeleton() -> None:
    task = LeanTaskPackage(
        leantask_id="finite_tree_edge_count_L1",
        unit_id="finite_tree_edge_count",
        level=LeanTaskLevel.L1,
        informal_statement="Let G be a finite tree.",
        imports=["Mathlib.Combinatorics.SimpleGraph.Acyclic"],
        formal_target="G.edgeFinset.card + 1 = Fintype.card V",
        hypotheses=["V : Type*", "[Fintype V]", "G : SimpleGraph V", "hG : G.IsTree"],
        proof_path="existing theorem alignment",
        next_action="Check against pinned mathlib.",
    )

    rendered = render_leantask(task)

    assert "import Mathlib.Combinatorics.SimpleGraph.Acyclic" in rendered
    assert "theorem finite_tree_edge_count_L1" in rendered
    assert "(V : Type*) [Fintype V] (G : SimpleGraph V)" in rendered
    assert "([Fintype V])" not in rendered
    assert "G.edgeFinset.card + 1 = Fintype.card V" in rendered
    assert "sorry" in rendered


def test_render_l2_leantask_includes_alignment_report_and_sub_lemmas() -> None:
    task = LeanTaskPackage(
        leantask_id="finite_tree_edge_count_L2",
        unit_id="finite_tree_edge_count",
        level=LeanTaskLevel.L2,
        informal_statement="Let G be a finite tree.",
        imports=["Mathlib.Combinatorics.SimpleGraph.Acyclic"],
        formal_target="G.edgeFinset.card + 1 = Fintype.card V",
        hypotheses=["V : Type*", "[Fintype V]", "G : SimpleGraph V", "hG : G.IsTree"],
        alignment_declarations=["SimpleGraph.IsTree.card_edgeFinset"],
        sub_lemmas=[
            LeanSubLemma(
                lemma_id="finite_tree_edge_count_alignment",
                hypotheses=["V : Type*", "[Fintype V]", "G : SimpleGraph V", "hG : G.IsTree"],
                statement="G.edgeFinset.card + 1 = Fintype.card V",
            )
        ],
        next_action="Replace sorry sub-lemmas with alignment proof.",
    )

    rendered = render_leantask(task)

    assert "Existing-theorem alignment report:" in rendered
    assert "- SimpleGraph.IsTree.card_edgeFinset" in rendered
    assert "lemma finite_tree_edge_count_alignment" in rendered
    assert "theorem finite_tree_edge_count_L2" in rendered


def test_render_l1_preserves_implicit_binder_braces() -> None:
    task = LeanTaskPackage(
        leantask_id="category_theory_pullback_equivalence_L1",
        unit_id="category_theory_pullback_equivalence",
        level=LeanTaskLevel.L1,
        informal_statement="Pullback transport under equivalence.",
        imports=["Mathlib.CategoryTheory.Limits.Shapes.Pullbacks"],
        formal_target="HasPullback (e.functor.map f) (e.functor.map g)",
        hypotheses=["{X Y Z : C}", "f : X ⟶ Z", "g : Y ⟶ Z", "[HasPullback f g]"],
        next_action="Typecheck skeleton.",
    )

    rendered = render_leantask(task)

    assert "{X Y Z : C}" in rendered
    assert "({X Y Z : C})" not in rendered


def test_validate_l2_requires_alignment_and_sub_lemmas() -> None:
    task = LeanTaskPackage(
        leantask_id="finite_tree_edge_count_L2",
        unit_id="finite_tree_edge_count",
        level=LeanTaskLevel.L2,
        informal_statement="Let G be a finite tree.",
        formal_target="G.edgeFinset.card + 1 = Fintype.card V",
        next_action="Complete alignment proof.",
    )

    with pytest.raises(ArtifactValidationError) as excinfo:
        validate_leantask_package(task)

    message = str(excinfo.value)
    assert "missing_alignment_declarations" in message
    assert "missing_sub_lemmas" in message


def test_finite_tree_l2_example_validates() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    task = load_leantask_package(root / "examples" / "finite_tree" / "leantask_L2.json")
    assert task.level == LeanTaskLevel.L2
    assert task.alignment_declarations
