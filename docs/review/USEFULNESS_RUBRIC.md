# External Usefulness Rubric

This rubric scores whether a readiness report would help an external mathematician or formalizer act on the unit without project-internal context. Scores feed the structured review submission (`rubric_scores` in `docs/review/templates/readiness_report_review.json`).

## Scale

| Score | Label | Meaning |
|-------|-------|---------|
| 1 | Poor | Misleading or unusable for external action |
| 2 | Weak | Major gaps; reader must redo most assessment |
| 3 | Adequate | Usable with moderate additional investigation |
| 4 | Strong | Clear guidance with minor gaps only |
| 5 | Excellent | External reader can proceed confidently |

## Dimensions

### Source fidelity (`source_fidelity`)

Does the report faithfully reflect the informal statement and proof in the unit?

| Score | Criteria |
|-------|----------|
| 1 | Report contradicts or ignores the source statement or proof |
| 2 | Major elements of the source are missing or mislabeled |
| 3 | Core content captured; secondary details incomplete |
| 4 | Statement, context, and proof strategy aligned with minor omissions |
| 5 | Complete and precise alignment with the source text |

### Actionability (`actionability`)

Can an external reader determine what to do next?

| Score | Criteria |
|-------|----------|
| 1 | No credible next step |
| 2 | Next step vague or inconsistent with blockers |
| 3 | General direction clear; priorities ambiguous |
| 4 | Clear next action with justified tradeoffs |
| 5 | Next action is specific, ordered, and immediately executable |

### Library alignment (`library_alignment`)

Are existing-theorem candidates responsible and checkable?

| Score | Criteria |
|-------|----------|
| 1 | Candidates invented or clearly wrong |
| 2 | Names plausible but unsupported by evidence |
| 3 | At least one candidate plausibly related; verification still required |
| 4 | Candidates justified by domain knowledge or index lookup |
| 5 | Candidates verified against mathlib or marked as confirmed alignment |

### Blocker specificity (`blocker_specificity`)

Do blockers name concrete formalization gaps?

| Score | Criteria |
|-------|----------|
| 1 | Blockers absent, generic, or duplicate list fields without insight |
| 2 | Blockers vague (for example, "needs formalization") |
| 3 | Blockers identify topic areas but not specific alignment decisions |
| 4 | Blockers name specific definitions, representations, or infrastructure gaps |
| 5 | Blockers are minimal, non-overlapping, and map cleanly to next actions |

### Path clarity (`path_clarity`)

Is the constructive path coherent relative to the informal proof?

| Score | Criteria |
|-------|----------|
| 1 | Path missing or unrelated to the source proof |
| 2 | Path skips essential proof steps |
| 3 | Path covers main steps but ordering or dependencies unclear |
| 4 | Path mirrors proof strategy with explicit missing lemmas |
| 5 | Path is ordered, complete, and distinguishes reuse vs construction |

## Promotion thresholds

These thresholds guide tier promotion. They are guidelines, not automatic rules.

| Target tier | Minimum per-dimension score | Additional requirements |
|-------------|----------------------------|------------------------|
| Silver | 3 on all dimensions | Dimension review flags pass or corrections provided |
| Gold | 4 on all dimensions | Expert verification of library candidates and blockers |

Reports with any dimension scored 1 should not be promoted. Score 2 requires explicit justification in reviewer `notes`.

## Mapping to ReadinessBench

Rubric scores are stored in review submissions for audit and inter-annotator analysis. ReadinessBench evaluation itself scores predicted reports against Gold list fields (candidates, constructive path, blockers). High rubric scores correlate with Gold quality but do not replace Gold fixture review.
