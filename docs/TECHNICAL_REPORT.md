# Wave 6 Technical Report

## Summary

Wave 6 delivers the v0.2.0 public release: ReadinessBench gold fixtures at benchmark scale, deterministic Atlas blocker clustering, versioned release manifests, Docker/RQ infrastructure, and published documentation for external evaluators.

## ReadinessBench scale

The benchmark manifest includes 43 items across three tiers:

| Tier | Count | Role |
|------|-------|------|
| Gold | 11 | Expert-reviewed evaluated truth |
| Silver | 1 | Promotion workflow example |
| Bronze | 31 | Corpus-scale candidate units |

Gold items span graph theory, category theory, algebra, topology, analysis, number theory, linear algebra, measure theory, logic, and set theory. Each gold item includes a reviewed theorem/proof unit, readiness report, and Atlas record suitable for public export.

The hand-authored reference stacks at `examples/finite_tree/` and `examples/category_theory_pullback/` remain the primary onboarding path. The category-theory example is examples-only until promoted through external review.

## Corpus ingestion

Wave 1 shipped five author-permitted LaTeX sources under `corpus/sources/` with mixed release modes. Deterministic ingestion produced 30 theorem/proof units with preserved source spans. Bronze benchmark promotion populated 31 bronze manifest entries from corpus units.

## Atlas blocker clustering

Gold readiness-report blockers are normalized and clustered deterministically by lowercase token collapse. Cluster identifiers are SHA-256 prefixes of normalized blocker text, ensuring stable reports across repeated runs and platforms.

The `generate-atlas-clusters` CLI command writes `public_exports/atlas_clusters.json`, which feeds release packaging and external analysis of recurring formalization gaps.

## Release manifests

The `build-release-manifest` CLI command checksums public export artifacts and records schema versions in `releases/<version>/manifest.json`. The v0.2.0 manifest lives at `releases/v0.2.0/manifest.json`.

## Infrastructure

Docker Compose provides API (`:8000`), review UI (`:8080`), Redis-backed RQ worker, and an optional Lean profile. Job metadata uses SQLite at `FRE_JOBS_DB` for v0; PostgreSQL remains deferred. See `docs/DOCKER.md`.

## Documentation and CI

MkDocs builds the public documentation site from `docs/` with navigation for architecture, demo, release, Docker, corpus governance, and review workflows. CI runs the documentation build on every push and pull request. The test suite includes 352 unit tests (run `pytest --collect-only -q` on HEAD). The stabilization sprint added `review_origin` on gold exports, LF-normalized release checksums, and a `make smoke` gate (`setup`, `test`, `validate-examples`, `validate-readinessbench`, `verify-release-manifest`, `docs`).

## Evaluation guidance

External evaluators should:

1. Validate the committed ReadinessBench manifest (`make validate-readinessbench`).
2. Produce schema-valid predicted readiness reports for each gold `unit_id`.
3. Run `make run-readinessbench` with a predictions directory.
4. Compare Atlas cluster reports across model versions to track blocker regressions.

### Lexical F1 baseline (v0.2)

ReadinessBench macro-F1 uses normalized set overlap on string lists (theorem candidates, constructive paths, blockers, notation fields). Scores reflect **lexical** agreement with gold strings, not semantic correctness or mathlib declaration equivalence. A semantically relevant prediction that uses different naming can score 0.0. Treat v0.2 metrics as a reproducible baseline, not a claim of formalization quality. Semantic metrics are planned for v0.3.

## Limitations

Wave 6 does not claim end-to-end automated formalization. Model outputs remain candidate artifacts until reviewed. Lean typechecking for L1/L2 tasks remains a local or optional CI workflow (`workflow_dispatch`). The review UI is a thin inspection surface; full in-browser annotation is optional follow-on work.
