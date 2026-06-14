import Mathlib.CategoryTheory.Limits.Shapes.Pullbacks
import Mathlib.CategoryTheory.Equivalence

/-
LeanTask: category_theory_pullback_equivalence_L1
Unit: category_theory_pullback_equivalence
Level: L1

Informal statement:
Let C and D be categories and F : C ≃ D an equivalence of categories. If a cospan (f : X → Z, g : Y → Z) admits a pullback (P, π₁, π₂) in C, then (F f, F g) admits a pullback (F P, F π₁, F π₂) in D.

Next action:
Typecheck this skeleton against the pinned lean/ Lake project and refine imports.

Proof path:
apply Equivalence.preservesLimitsOfShape to the pullback diagram

Fallback path:
sorry-based cone transport skeleton
-/

theorem category_theory_pullback_equivalence_L1 (C : Type u) [Category C] (D : Type v) [Category D] (e : C ≌ D) {X Y Z : C} (f : X ⟶ Z) (g : Y ⟶ Z) [HasPullback f g] :
    HasPullback (e.functor.map f) (e.functor.map g) := by
  sorry
