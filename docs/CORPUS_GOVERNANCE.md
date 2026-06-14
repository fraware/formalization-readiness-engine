# Corpus governance

This document defines how curated LaTeX sources enter the Formalization Readiness Engine corpus, how release modes constrain public exports, and how ingested units graduate into ReadinessBench bronze tier.

## Catalog schema

Each source in `corpus/catalog.json` is a `SourceDocument` with:

| Field | Purpose |
| --- | --- |
| `source_id` | Stable identifier referenced by ingested units |
| `source_type` | Provenance class (e.g. `author_permitted_notes`) |
| `license_status` | Permission state (e.g. `permission_granted`) |
| `release_mode` | Export policy (see below) |
| `domain` | Mathematical domain label carried into units |
| `path` | Repository-relative path to the LaTeX source |
| `curator` | Optional maintainer contact |
| `permission_reference` | Optional citation for author permission |

Validation (`make validate-corpus-catalog` or `fre_core.cli validate-corpus-catalog`) enforces:

- At least one source with `release_mode=full_text_allowed`
- At least one source with `release_mode=metadata_only` (licensing leak-test coverage)
- Unique `source_id` values and existing source files under `--repo-root`

## Release modes

- **`full_text_allowed`** — statement and proof text may appear in shareable exports.
- **`metadata_only`** — only derived records (unit ids, spans, domain) may be exported; statement/proof text is stripped.
- **`derived_annotations_only`** — reserved for future annotation-only sources.

Use `export-shareable-units` with `include_text=False` to produce metadata-only exports. Public benchmark export applies the same rules when a catalog is supplied.

## Author-permitted LaTeX sources

Wave 1 ships five curriculum sources under `corpus/sources/`:

1. `finite_tree.tex` — graph theory, trees and edge counts
2. `category_theory_pullback.tex` — pullbacks preserved by equivalences
3. `graph_theory_basics.tex` — handshaking lemma, connectivity, forests
4. `category_theory_limits.tex` — limits, pullbacks as limits
5. `metadata_only_graph_sketch.tex` — metadata-only leak-test sketch

Each file begins with an author-permission header documenting curator contact and redistribution terms. Do not ingest third-party LaTeX without an equivalent header and catalog metadata.

## Ingestion workflow

Deterministic ingestion parses `theorem`, `lemma`, `proposition`, `corollary`, `definition`, and `remark` environments, preserving byte spans into `statement_span` and `proof_span`.

```bash
make validate-corpus-catalog
make ingest-catalog
```

`ingest-catalog` writes unit JSON to `corpus/units/`. Pass `--repair` to invoke the segmentation repair scaffold when deterministic parsing is insufficient (requires a structured model client).

## Swapping in user sources

To replace or extend the corpus:

1. Add or update a LaTeX file under `corpus/sources/` with a permission header.
2. Append or edit an entry in `corpus/catalog.json` pointing at the new path.
3. Run `make validate-corpus-catalog` then `make ingest-catalog`.
4. Review ingested units under `corpus/units/` before promotion.

Keep `metadata_only` sources in the catalog to validate export stripping after any catalog change.

## Bronze benchmark promotion

Ingested units are promoted into ReadinessBench bronze tier with machine-generated readiness placeholders:

```bash
fre_core.cli promote-benchmark-units corpus/units --overwrite
fre_core.cli promote-benchmark-item corpus/units/<unit_id>.json
```

Promotion writes `benchmarks/readinessbench/bronze/<unit_id>/unit.json` and `readiness_report.json`, then appends manifest entries. Manifest and gold truth paths must not reference `artifacts/generated/`; validation rejects generated-artifact escapes. ReadinessBench prediction inputs may use `artifacts/generated/` (for example live demo output) without entering the benchmark tree.

Gold and silver tiers remain expert-reviewed subsets; bronze holds corpus-scale candidate units awaiting extraction passes in later waves.

## Phase 2 exit criteria

- Five catalog sources with mixed release modes
- Thirty ingested units with preserved spans (`corpus/units/`)
- Bronze manifest populated from corpus units (31 bronze items in ReadinessBench)
- Metadata-only source included for licensing leak tests
