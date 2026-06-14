import Mathlib.CategoryTheory.Limits.Shapes.Pullbacks
import Mathlib.CategoryTheory.Equivalence

open CategoryTheory

/-
This file is an initial Lean-facing target for the category-theory pullback example.
It should be treated as an alignment candidate until checked against the pinned
mathlib version used by the project.
-/

example {C : Type u} [Category C] {D : Type v} [Category D] (e : C ≌ D)
    {X Y Z : C} (f : X ⟶ Z) (g : Y ⟶ Z) [HasPullback f g] :
    HasPullback (e.functor.map f) (e.functor.map g) := by
  exact e.functor.preservesPullback f g
