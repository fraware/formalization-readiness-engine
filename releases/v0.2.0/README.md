# Release v0.2.0 (frozen snapshot)

This directory is the **committed public release bundle** for Formalization Readiness Engine v0.2.0. It is a frozen snapshot, not a live view of the current development branch.

## Snapshot identity

| Field | Value |
|-------|-------|
| Release version | `v0.2.0` |
| Frozen git commit | [`56e48e83e760df24d35359ed230d934debadd094`](https://github.com/fraware/formalization-readiness-engine/commit/56e48e83e760df24d35359ed230d934debadd094) |
| Manifest | [`manifest.json`](manifest.json) |

The `git_commit` in `manifest.json` records the repository state when this bundle was cut. **Current `main` may be ahead** of that commit; development continues independently of this directory.

## Contents

| Path | Role |
|------|------|
| [`manifest.json`](manifest.json) | Release metadata, schema versions, and SHA-256 checksums for committed exports |
| [`exports/readinessbench.jsonl`](exports/readinessbench.jsonl) | Public ReadinessBench JSONL (43 items: 11 gold, 1 silver, 31 bronze) |
| [`exports/atlas.jsonl`](exports/atlas.jsonl) | Formalization Gap Atlas records |
| [`exports/atlas_clusters.json`](exports/atlas_clusters.json) | Deterministic blocker clusters from gold readiness reports |

Checksums in `manifest.json` apply to files under **`releases/v0.2.0/exports/`**, not to regenerated output in gitignored `public_exports/`.

## Verify locally

```bash
make verify-release-manifest
```

## Regenerate vs release

Local export commands write to `public_exports/` for inspection:

```bash
make export-public-benchmark
make export-public-atlas
```

Refreshing this frozen bundle requires copying byte-identical outputs into `releases/v0.2.0/exports/`, running `make build-release-manifest`, and cutting a new release tag. Do not update `manifest.json` `git_commit` on every push to `main`.

See [`docs/PUBLIC_RELEASE.md`](../../docs/PUBLIC_RELEASE.md) for the full public-release workflow and release semantics.
