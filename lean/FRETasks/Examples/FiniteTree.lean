import Mathlib.Combinatorics.SimpleGraph.Acyclic

open SimpleGraph

/-
This file is an initial Lean-facing target for the finite-tree example.
It should be treated as an alignment candidate until checked against the
pinned mathlib version used by the project.
-/

example {V : Type*} [Fintype V] (G : SimpleGraph V) [Fintype G.edgeSet]
    (hG : G.IsTree) :
    G.edgeFinset.card + 1 = Fintype.card V := by
  simpa using hG.card_edgeFinset
