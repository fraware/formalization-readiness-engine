import Mathlib.Combinatorics.SimpleGraph.Acyclic

/-
LeanTask: finite_tree_edge_count_L1
Unit: finite_tree_edge_count
Level: L1

Informal statement:
Let G=(V,E) be a finite tree. Then |E| = |V| - 1.

Next action:
Replace sorry with an alignment proof against the pinned mathlib theorem.

Proof path:
existing theorem alignment candidate (SimpleGraph.IsTree.card_edgeFinset)

Fallback path:
constructive decomposition into leaf-removal tasks
-/

theorem finite_tree_edge_count_L1 (V : Type*) [Fintype V] (G : SimpleGraph V) [Fintype G.edgeSet] (hG : G.IsTree) :
    G.edgeFinset.card + 1 = Fintype.card V := by
  sorry
