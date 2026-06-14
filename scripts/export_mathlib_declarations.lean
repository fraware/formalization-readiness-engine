/-
Smoke export for mathlib declaration JSONL. CI uses build-ci-fixture instead.
-/
import Lean
open Lean
unsafe def main : IO Unit := do
  IO.println "{\"declaration_id\":\"mathlib:SimpleGraph.IsTree.card_edgeFinset\",\"full_name\":\"SimpleGraph.IsTree.card_edgeFinset\",\"namespace\":\"SimpleGraph.IsTree\",\"module\":\"Mathlib.Combinatorics.SimpleGraph.Acyclic\",\"kind\":\"theorem\",\"type_signature\":null,\"docstring\":null}"
main
