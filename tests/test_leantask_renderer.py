from fre_core.leantask_renderer import render_leantask
from fre_core.schemas import LeanTaskLevel, LeanTaskPackage


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
