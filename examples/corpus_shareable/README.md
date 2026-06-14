# Corpus shareable export example

This directory demonstrates how catalog release modes filter theorem/proof units for sharing.

## Layout

| Path | Purpose |
|------|---------|
| `catalog.json` | Two sources: `full_text_allowed` and `metadata_only` |
| `sources/` | Permitted LaTeX inputs referenced by the catalog |
| `ingested/` | Units parsed from catalog sources (all catalog source IDs) |
| `full_text_export/` | Shareable units with statement and proof text retained |
| `metadata_only_export/` | Shareable units with text stripped for metadata-only sources |

## Regenerate

From the repository root:

```bash
python -m fre_core.cli ingest-catalog examples/corpus_shareable/catalog.json examples/corpus_shareable/ingested
python -m fre_core.cli export-shareable-units examples/corpus_shareable/ingested examples/corpus_shareable/catalog.json examples/corpus_shareable/full_text_export --include-text
python -m fre_core.cli export-shareable-units examples/corpus_shareable/ingested examples/corpus_shareable/catalog.json examples/corpus_shareable/metadata_only_export
```

On Windows:

```powershell
python -m fre_core.cli ingest-catalog examples/corpus_shareable/catalog.json examples/corpus_shareable/ingested
python -m fre_core.cli export-shareable-units examples/corpus_shareable/ingested examples/corpus_shareable/catalog.json examples/corpus_shareable/full_text_export --include-text
python -m fre_core.cli export-shareable-units examples/corpus_shareable/ingested examples/corpus_shareable/catalog.json examples/corpus_shareable/metadata_only_export
```

The full-text export includes only sources with `release_mode: full_text_allowed`. The metadata-only export keeps unit identifiers and spans but clears statement and proof text for restricted sources.
