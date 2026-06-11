import Lake
open Lake DSL

package FRETasks where
  -- Lean-facing task examples for the Formalization Readiness Engine.

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git"

lean_lib FRETasks where
  roots := #[`FRETasks]
