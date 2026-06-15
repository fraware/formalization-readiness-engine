# Public Release Guide

This document explains how external users inspect examples, run ReadinessBench, and consume public JSONL exports from the Formalization Readiness Engine.

## Release semantics

A **public release** is a frozen, checksum-verified bundle under `releases/<version>/`, not whatever happens to be on `main` at checkout time.

| Concept | Meaning |
|---------|---------|
| Frozen snapshot | `releases/v0.2.0/` records a specific `git_commit` in `manifest.json` plus committed exports whose SHA-256 checksums are listed in that manifest |
| Current development | The checked-out branch (typically `main`) may advance after the snapshot was cut; only a new tag and manifest update creates a new public release |
| Local regeneration | `make export-public-benchmark` and `make export-public-atlas` write to gitignored `public_exports/` for inspection; they do not replace the frozen bundle unless you intentionally copy outputs and rebuild the manifest |
| Manifest updates | Run `make build-release-manifest` only when cutting a release (see `.github/workflows/release.yml`); do not bump `git_commit` on every push |

Verify a committed bundle:

```bash
make verify-release-manifest
```

## v0.2.0 release

The committed public release is version v0.2.0, frozen at git commit [`f411fd5f1a6b6e4a5624970a26d1c33614b17f0b`](https://github.com/fraware/formalization-readiness-engine/commit/f411fd5f1a6b6e4a5624970a26d1c33614b17f0b) (release bundle cut). Lean skeleton verification is documented separately at `56e48e83` in [`lean/README.md`](../lean/README.md).

- Release manifest: `releases/v0.2.0/manifest.json` (see also `releases/v0.2.0/README.md`)
- Committed release exports: `releases/v0.2.0/exports/readinessbench.jsonl`, `releases/v0.2.0/exports/atlas.jsonl`, `releases/v0.2.0/exports/atlas_clusters.json`
- ReadinessBench: 43 manifest items (11 gold, 1 silver, 31 bronze)
- JSON Schemas: `schemas/`

Regenerate exports locally with `make export-public-benchmark` and `make export-public-atlas` (written to gitignored `public_exports/`). Copy byte-identical outputs into `releases/<version>/exports/` and rebuild the release manifest with `make build-release-manifest`.

## What is published

The repository publishes structured artifacts, not chat transcripts.

| Export | Path | Contents |
|--------|------|----------|
| ReadinessBench | `releases/v0.2.0/exports/readinessbench.jsonl` | Bronze, Silver, and Gold benchmark items with shareable units and readiness reports |
| Formalization Gap Atlas | `releases/v0.2.0/exports/atlas.jsonl` | Curated Atlas records from reference examples and reviewed benchmark items |
| Atlas clusters | `releases/v0.2.0/exports/atlas_clusters.json` | Deterministic blocker clusters from gold readiness reports |
| JSON Schemas | `schemas/` | Public artifact contracts exported from Pydantic models |

Each JSONL export has a companion manifest (`*.manifest.json`) documenting `export_id`, `export_type`, `record_count`, and `output_path`.

## Generate exports locally

From the repository root:

```bash
make export-public-benchmark
make export-public-atlas
```

These commands write to gitignored `public_exports/` for local regeneration. To refresh a versioned release bundle, copy the outputs into `releases/<version>/exports/` and run `make build-release-manifest`.

On Windows:

```powershell
.\scripts\dev.ps1 export-public-benchmark
.\scripts\dev.ps1 export-public-atlas
```

Optional corpus catalog filtering strips restricted source text according to `release_mode`:

```bash
PYTHONPATH=packages/fre_core/src:. python -m fre_core.cli export-public-benchmark \
  --catalog-path examples/corpus_shareable/catalog.json
```

## ReadinessBench for external evaluators

1. Validate the committed manifest:

```bash
make validate-readinessbench
```

2. Produce predicted readiness reports for gold `unit_id` values (schema-valid JSON only).
3. Score predictions against gold fixtures:

```bash
make run-readinessbench PREDICTIONS_DIR=path/to/predictions
```

Predictions may be nested as `predictions/<unit_id>/readiness_report.json`, flat as `predictions/<unit_id>.json`, or in demo-live layout as `predictions/<example_key>/readiness_report.model.json` (matched by `unit_id` in the JSON).

Only gold items participate in scoring. Items without a matching prediction are skipped; at least one scored gold item is required. See `benchmarks/readinessbench/README.md` for tier definitions.

## Inspect reference examples

Hand-authored artifact stacks live under:

- `examples/finite_tree/`
- `examples/category_theory_pullback/`

Validate an example directory:

```bash
PYTHONPATH=packages/fre_core/src:. python -m fre_core.cli validate-example-dir examples/finite_tree
```

## Review API and thin UI

Install API dependencies and start the backend:

```bash
make setup-api
make run-api
```

Serve the minimal review UI:

```bash
make run-review-ui
```

Open `http://127.0.0.1:8080`. The UI loads example artifacts and posts review submissions to:

- `POST /validate/readiness-report`
- `POST /validate/review-submission`
- `POST /align/readiness-report`

See `apps/review-ui/README.md` for details. For Docker deployment, see `docs/DOCKER.md`.

## mathlib alignment

Alignment proposes candidate declarations only. Confirmed alignment requires explicit reviewer flags and is never auto-promoted from retrieval scores.

```bash
PYTHONPATH=packages/fre_core/src:. python -m fre_core.cli align-readiness-report \
  examples/finite_tree/readiness_report.json \
  artifacts/generated/finite_tree/alignment.json \
  --unit-path examples/finite_tree/unit.json
```

## Licensing and release modes

Public exports respect corpus `release_mode` values:

- `full_text_allowed`: statement and proof text may appear in exported units.
- `metadata_only`: exported units have empty `statement` and `proof`.
- `derived_annotations_only`: derived records may be shared without source text.

CI runs a licensing leak test ensuring metadata-only sources never appear with full statement or proof text in public exports. Run it locally:

```bash
PYTHONPATH=packages/fre_core/src:. pytest tests/test_public_export.py -q -k "licensing or metadata_only"
```

See `docs/CORPUS_GOVERNANCE.md` for catalog policy.

## Gold provenance disclaimer

v0.2 gold items are labeled `review_origin: internal_seed` in public exports. They are curated internal fixtures for reproducible evaluation, not externally validated community benchmark truth. Promoting an item to `external_expert` requires a persisted review submission on disk (not the template placeholder) and a matching changelog entry.

## JSONL record shapes

### Benchmark item

```json
{
  "schema_version": "0.1",
  "record_type": "benchmark_item",
  "item_id": "finite_tree_edge_count_gold",
  "unit_id": "finite_tree_edge_count",
  "tier": "gold",
  "review_origin": "internal_seed",
  "unit": { "...": "TheoremProofUnit" },
  "readiness_report": { "...": "ReadinessReport with review_origin" }
}
```

### Atlas record

```json
{
  "schema_version": "0.1",
  "record_type": "atlas",
  "unit_id": "finite_tree_edge_count",
  "source_id": "hand_authored_finite_tree_001",
  "domain": "graph_theory",
  "atlas_record": { "...": "AtlasRecord" },
  "unit": { "...": "TheoremProofUnit or null" }
}
```

Schema files: `schemas/public_benchmark_export_record.schema.json`, `schemas/public_atlas_export_record.schema.json`, `schemas/public_export_manifest.schema.json`.

## Citation

```text
Formalization Readiness Engine (v0.2.0).
https://github.com/fraware/formalization-readiness-engine
Release manifest: releases/v0.2.0/manifest.json
```

## Public release checklist

Before tagging a new public release:

1. Run `make check` and `make demo`.
2. Regenerate `public_exports/`, copy into `releases/<version>/exports/`, and verify licensing leak tests pass.
3. Run `make build-release-manifest` and commit `releases/<version>/manifest.json` plus `releases/<version>/exports/`.
4. Run `make verify-release-manifest` to confirm checksums match.
5. Update `docs/TECHNICAL_REPORT.md` and ReadinessBench counts in `README.md`.
6. Run `make docs` and confirm the site builds.
