# Baseline error taxonomy

Wave 3 baseline evaluation categorizes prediction errors against committed reference
examples. Each category corresponds to one readiness-report field group or companion
artifact slice.

## Categories

- `notation`: readiness report notation dimension mismatch
- `blockers`: readiness report blocker list mismatch
- `wrong_candidates`: existing theorem candidate list mismatch
- `constructive_path`: constructive path list mismatch
- `proofgraph_nodes`: proof graph node set mismatch
- `proofgraph_edges`: proof graph edge set mismatch
- `atlas_evidence`: Atlas evidence field mismatch
- `atlas_blocker_type`: Atlas blocker_type field mismatch
- `atlas_recommended_action`: Atlas recommended_action field mismatch
- `leantask_imports`: LeanTask imports list mismatch
- `leantask_hypotheses`: LeanTask hypotheses list mismatch
- `leantask_formal_target`: LeanTask formal_target mismatch

## Aggregation

`aggregate_error_summaries` counts category hits per unit and reports `unit_count`,
`total_errors`, and per-category counts in `categories.<name>.count` with rates.
