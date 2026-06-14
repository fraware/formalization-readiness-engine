# Artifacts directory

This tree holds generated and scratch artifacts. It is separate from reviewed example and benchmark data.

## Layout

| Path | Purpose | Committed to git? |
|------|---------|-------------------|
| `artifacts/generated/` | Model outputs, demo runs, and local evaluation scratch | Partially (templates only; most paths gitignored) |
| `artifacts/generated/demo_run/offline/` | Offline demo outputs per example | No (gitignored) |
| `artifacts/generated/demo_run/live/` | Live demo candidate artifacts | No (gitignored) |
| `examples/finite_tree/` | Hand-authored reference stack for the first demo | Yes (reviewed examples) |
| `examples/category_theory_pullback/` | Hand-authored category-theory reference stack | Yes (reviewed examples) |
| `benchmarks/readinessbench/` | ReadinessBench manifest and Bronze/Silver/Gold fixtures (43 items) | Yes (gold is evaluated truth) |
| `examples/corpus_shareable/` | Corpus shareable export demo | Yes (reviewed examples) |
| `corpus/units/` | Ingested theorem/proof units from catalog sources (30 units) | Yes |
| `corpus/` | Source catalog and permitted LaTeX inputs | Yes |
| `public_exports/` | Ephemeral local export output (gitignored; regenerate with Makefile targets) | No |
| `releases/v0.2.0/exports/` | Committed public JSONL exports for v0.2.0 | Yes |

## Rules

1. Never copy generated model output into `examples/` or `benchmarks/readinessbench/gold/` without human review.
2. Candidate artifacts must keep `review_status: candidate` until review promotes them.
3. ReadinessBench scoring uses gold items only; bronze and silver document the promotion path.
4. After live extraction, write evaluation notes to `artifacts/generated/<example>/NOTES.md`.

## Demo outputs

The end-to-end demo writes per-example outputs under `artifacts/generated/demo_run/`:

```text
artifacts/generated/demo_run/offline/<example_key>/
artifacts/generated/demo_run/live/<example_key>/
```

See `docs/DEMO.md` for the full pipeline and environment variables.

## Corpus workflow

```bash
make ingest-corpus
make export-corpus-shareable
```

See `examples/corpus_shareable/README.md` for release-mode export details and `docs/CORPUS_GOVERNANCE.md` for catalog policy.
