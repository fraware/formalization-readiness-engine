# Live extraction evidence — category theory pullback

**Example:** `category_theory_pullback` (`category_theory_pullback_equivalence`)
**Source artifacts:** `artifacts/generated/demo_run/live/category_theory_pullback/`
**Gold reference:** `benchmarks/readinessbench/gold/category_theory_pullback_equivalence/`

## Evaluation scores (ReadinessBench gold)

| Metric | Score |
|--------|------:|
| macro F1 (lexical v0.2) | 0.0 |
| existing theorem candidates F1 (lexical) | 0.0 |
| constructive path F1 | 0.0 |
| blockers F1 | 0.0 |
| notation readiness F1 | 0.0 |
| v0.3 macro F1 | 0.833333 |
| theorem candidates F1 (declaration-ID v0.3) | 0.666667 |

## Validation (tiered)

Gold fixtures use strict validation; live candidate artifacts use permissive validation.
ProofGraph and Atlas public_export checks apply after artifact normalization.

- `atlas_record.model.json` strict: fail, permissive: pass, public_export (normalized): pass
- `proofgraph.model.json` strict: fail, permissive: pass, public_export (normalized): pass
- `readiness_report.model.json` strict: pass, permissive: pass, public_export (normalized): pass

## Theorem candidate comparison

- **Predicted:** CategoryTheory.Limits.hasPullback_of_equivalence, CategoryTheory.Limits.isLimit.mapConeEquivalence
- **Gold:** CategoryTheory.Equivalence.preservesLimitsOfShape, CategoryTheory.Limits.PreservesPullback

## What worked

- **Statement recovery:** The model captured the pullback-stability statement under a categorical equivalence with accurate informal wording.
- **Dependency awareness:** Generated text references `CategoryTheory.Equivalence`, cones, and limit-preservation concepts appropriate to the domain.
- **Actionability:** `recommended_next_action` points to cone-category equivalence construction, which is a reasonable formalizer next step.

## Error analysis

### False candidates

- The model proposed `CategoryTheory.Limits.hasPullback_of_equivalence` and `CategoryTheory.Limits.isLimit.mapConeEquivalence`. Gold expert-reviewed candidates are `CategoryTheory.Equivalence.preservesLimitsOfShape` and `CategoryTheory.Limits.PreservesPullback`. Names differ entirely, yielding zero overlap F1 despite thematic relevance.

### Blocker quality

- Predicted blockers are high-level uncertainty statements ("uncertain if equivalence of cone categories exists"). Gold blockers enumerate concrete alignment gaps: equivalence vs isomorphism, unit/counit transport, reuse-vs-construct decision, and specific Mathlib module targets.

### Constructive path drift

- The model lists a four-step cone-transport proof sketch. Gold path aligns Mathlib `Equivalence`, imports limit-preservation, specializes to pullback shape, proves cone-category equivalence, and packages hypotheses. Step granularity and naming diverge completely from gold.

### Notation readiness

- Model notes generic pullback/cone notation gaps but misses gold-specific items: equivalence symbol vs `CategoryTheory.Equivalence`, and transport along diagram isomorphisms.

### ProofGraph drift

- Generated graph introduces `derived_fact`, `construction_step`, `application_step`, and duplicate `justification` nodes. Gold graph is smaller and uses `library_candidate` / `blocker` nodes tied to reviewed alignment decisions.

### Atlas record

- Live atlas used a long free-form `blocker_type` string unrelated to gold `notation_alignment`. Strict atlas validation fails; permissive validation passes on evidence text alone.

## Recommended follow-up

1. Add retrieval or few-shot examples that show gold Mathlib theorem names for category-theory limits.
2. Post-process theorem candidates against the fixture declaration index before reporting.
3. Tighten blocker prompts to emit taxonomy-aligned labels plus source spans.

