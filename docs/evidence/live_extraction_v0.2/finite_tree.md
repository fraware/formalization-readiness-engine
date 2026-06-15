# Live extraction evidence — finite tree

**Example:** `finite_tree` (`finite_tree_edge_count`)
**Source artifacts:** `artifacts/generated/demo_run/live/finite_tree/`
**Gold reference:** `benchmarks/readinessbench/gold/finite_tree_edge_count/`

## Evaluation scores (ReadinessBench gold)

| Metric | Score |
|--------|------:|
| macro F1 (lexical v0.2) | 0.25 |
| existing theorem candidates F1 (lexical) | 1.0 |
| constructive path F1 | 0.0 |
| blockers F1 | 0.0 |
| notation readiness F1 | 0.0 |
| v0.3 macro F1 | 0.833333 |
| theorem candidates F1 (declaration-ID v0.3) | 1.0 |

## Validation (tiered)

Gold fixtures use strict validation; live candidate artifacts use permissive validation.
ProofGraph and Atlas public_export checks apply after artifact normalization.

- `atlas_record.model.json` strict: fail, permissive: pass, public_export (normalized): pass
- `proofgraph.model.json` strict: fail, permissive: pass, public_export (normalized): pass
- `readiness_report.model.json` strict: pass, permissive: pass, public_export (normalized): pass

## Theorem candidate comparison

- **Predicted:** SimpleGraph.IsTree.card_edgeFinset
- **Gold:** SimpleGraph.IsTree.card_edgeFinset

## What worked

- **Existing-theorem alignment:** The model correctly surfaced `SimpleGraph.IsTree.card_edgeFinset`, matching the gold candidate. Lexical alignment in `alignment.json` also ranked this declaration first.
- **Statement and context dimensions:** Both were marked `clear` with faithful paraphrases of the finite-tree edge-count statement.
- **Proof strategy shape:** The constructive path lists the standard induction-on-vertices outline (leaf removal, inductive step, cardinality update).

## Error analysis

### False or weak candidates

- Alignment returned related theorems (`card_edgeFinset'`, neighboring `SimpleGraph` declarations) with lower scores. None were emitted as false positives in `existing_theorem_candidates`, but reviewers should watch substring matches on primed names.

### Blocker quality

- Predicted blockers focus on leaf-existence and deletion APIs. Gold blockers additionally require **definition alignment** (tree, leaf, `G-v`) and an explicit **reuse-vs-construct** decision. The model under-specified notation alignment (`G-v`) and the strategic fork between direct theorem reuse and constructive decomposition.

### Constructive path drift

- Gold path decomposes into five checkable obligations (leaf existence, deletion formalization, tree preservation, vertex-count update, edge-count update). The model collapsed these into fewer, less Mathlib-specific steps, yielding zero constructive-path F1 despite plausible prose.

### ProofGraph drift

- Generated graph uses free-form node types (`theorem`, `base_case`, `inductive_step`) rather than the gold scaffold (`theorem_statement`, `library_candidate`, `blocker`). Nodes are semantically reasonable but not comparable to the reviewed graph without normalization.

### Atlas record

- Live atlas used `blocker_type: definition-gap` (not in the gold controlled vocabulary `notation_alignment`). Evidence is source-grounded, but taxonomy alignment failed strict validation.

## Recommended follow-up

1. Promote constructive-path prompts toward Mathlib-named subgoals.
2. Constrain atlas `blocker_type` to the gold vocabulary during extraction post-processing.
3. Normalize ProofGraph node types before benchmark comparison.

