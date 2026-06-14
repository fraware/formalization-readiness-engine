# Live extraction evidence (v0.2)

Committed reference scores and error analysis for the two model-backed demo examples. These files document what the live extraction pipeline produced on a recorded run; they are not a frozen release bundle.

## Files

| File | Contents |
|------|----------|
| [`summary.json`](summary.json) | Machine-readable index: recording timestamp, model and prompt versions, per-example ReadinessBench scores, validation outcomes, theorem candidate lists, and SHA-256 checksums of live artifacts under `artifacts/generated/demo_run/live/` |
| [`finite_tree.md`](finite_tree.md) | Human-readable score table, validation notes, theorem comparison, and error analysis for the finite-tree example (`finite_tree_edge_count`) |
| [`category_theory_pullback.md`](category_theory_pullback.md) | Same structure for the category-theory pullback example (`category_theory_pullback_equivalence`) |

## Recorded run metadata

From [`summary.json`](summary.json):

- **Recorded at:** 2026-06-14 (UTC)
- **Model:** `gpt-4.1`
- **Prompt version:** `6456c56e54c7` (content hash of extraction prompts; see `packages/fre_core/src/fre_core/extraction.py`)
- **Live artifact root:** `artifacts/generated/demo_run/live/`

## Regenerate

Requires `OPENAI_API_KEY` and model dependencies (`make setup-models`).

```bash
make demo-live
make record-live-extraction
```

On Windows:

```powershell
.\scripts\dev.ps1 demo-live
.\scripts\dev.ps1 record-live-extraction
```

`make record-live-extraction` runs `scripts/record_live_extraction.py`, which scores live outputs against gold fixtures, writes updated `summary.json`, and refreshes the per-example markdown reports. Commit the updated files if you intend to refresh the public reference scores.

To score without recording evidence:

```bash
make run-readinessbench PREDICTIONS_DIR=artifacts/generated/demo_run/live
```

## Lexical F1 caveat

ReadinessBench v0.2 scores use **lexical set-overlap F1**: predicted and gold label strings are normalized (case-folded, whitespace-collapsed) and compared as exact token sets. See `packages/fre_core/src/fre_core/evaluation.py` (`score_label_set`).

This baseline does **not** measure semantic equivalence. Consequences:

- **Theorem candidates** must match gold `full_name` strings exactly after normalization. Related Mathlib declarations with different names score zero even when mathematically relevant.
- **Category theory pullback** scored 0.0 macro F1 despite plausible informal extraction: predicted candidates (`CategoryTheory.Limits.hasPullback_of_equivalence`, `CategoryTheory.Limits.isLimit.mapConeEquivalence`) differ lexically from gold (`CategoryTheory.Equivalence.preservesLimitsOfShape`, `CategoryTheory.Limits.PreservesPullback`).
- **Constructive paths, blockers, and notation lists** require verbatim overlap with gold strings; paraphrases that a reviewer would accept still score zero.

Treat these scores as a reproducible v0.2 baseline for regression tracking, not as a complete quality judgment. Semantic and declaration-aware metrics are planned for v0.3; see `benchmarks/readinessbench/README.md` and `docs/TECHNICAL_REPORT.md`.
