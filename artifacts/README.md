# Artifacts directory

This tree holds generated and scratch artifacts. It is separate from reviewed example and benchmark data.

## Layout

| Path | Purpose | Committed to git? |
|------|---------|-------------------|
| `artifacts/generated/` | Model outputs and local evaluation scratch | No (gitignored) |
| `examples/finite_tree/` | Hand-authored reference stack for the first demo | Yes (reviewed examples) |
| `examples/corpus_shareable/` | Corpus shareable export demo (Sprint 3) | Yes (reviewed examples) |
| `corpus/` | Source catalog and permitted LaTeX inputs | Yes |

## Rules

1. Never copy generated model output into `examples/` or future gold benchmark paths without human review.
2. Candidate artifacts must keep `review_status: candidate` until review promotes them.
3. After live extraction, write notes to `artifacts/generated/<example>/NOTES.md` (local only).

## Corpus workflow (Sprint 3)

```bash
make ingest-corpus
make export-corpus-shareable
```

See `examples/corpus_shareable/README.md` for release-mode export details.
