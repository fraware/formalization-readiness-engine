import Mathlib.Combinatorics.SimpleGraph.Acyclic

/-
LeanTask: finite_tree_edge_count_L1
Unit: finite_tree_edge_count
Level: L1

Informal statement:
Let G=(V,E) be a finite tree. Then |E| = |V| - 1.

Next action:
Typecheck this skeleton against the pinned lean/ Lake project and confirm mathlib alignment.

Proof path:
existing theorem alignment candidate

Fallback path:
constructive decomposition into leaf-removal tasks
-/

theorem finite_tree_edge_count_L1 (V : Type*) [Fintype V] (G : SimpleGraph V) (hG : G.IsTree) :
    G.edgeFinset.card + 1 = Fintype.card V := by
  sorry
