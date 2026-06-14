# Wave 6 Technical Report

## Summary

Wave 6 delivers a public release of ReadinessBench gold fixtures, deterministic Atlas blocker clustering, versioned release manifests, and published documentation for external evaluators.

## ReadinessBench gold expansion

The benchmark manifest now includes eleven expert-reviewed gold items spanning graph theory, category theory, algebra, topology, analysis, number theory, linear algebra, measure theory, logic, and set theory. Each gold item includes a reviewed theorem/proof unit, readiness report, and Atlas record suitable for public export.

Bronze and silver tiers remain for the finite-tree reference item to preserve tier invariants and promotion workflow examples.

## Atlas blocker clustering

Gold readiness-report blockers are normalized and clustered deterministically by lowercase token collapse. Cluster identifiers are SHA-256 prefixes of normalized blocker text, ensuring stable reports across repeated runs and platforms.

The `generate-atlas-clusters` CLI command writes `public_exports/atlas_clusters.json`, which feeds release packaging and external analysis of recurring formalization gaps.

## Release manifests

The `build-release-manifest` CLI command checksums public export artifacts and records schema versions in `releases/<version>/manifest.json`. This supports reproducible public releases and audit trails for benchmark consumers.

## Documentation and CI

MkDocs builds the public documentation site from `docs/` with Wave 6 navigation entries. CI runs the documentation build on every push and pull request.

## Evaluation guidance

External evaluators should:

1. Validate the committed ReadinessBench manifest.
2. Produce schema-valid predicted readiness reports for each gold `unit_id`.
3. Run `make run-readinessbench` with a predictions directory.
4. Compare Atlas cluster reports across model versions to track blocker regressions.

## Limitations

Wave 6 does not claim end-to-end automated formalization. Model outputs remain candidate artifacts until reviewed. Lean typechecking for L1/L2 tasks remains a local or optional CI workflow.
