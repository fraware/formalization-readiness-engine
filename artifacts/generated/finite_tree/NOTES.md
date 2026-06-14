# Live baseline notes: finite_tree_edge_count

Local-only scratch notes for live model extraction on the finite-tree reference unit. Do not promote this file to Gold or Silver without review.

## Run metadata

| Field | Value |
|-------|-------|
| Unit ID | `finite_tree_edge_count` |
| Example path | `examples/finite_tree/` |
| Model | `gpt-4.1` (from `FRE_MODEL_NAME`) |
| Schema version | `0.1` |
| Run date (UTC) | `2026-06-14` |
| Operator | local Windows verification run |
| Output dir | `artifacts/generated/demo_run/live/finite_tree/` |

## Commands used

```bash
# Windows: install pip-system-certs first if OpenAI SSL fails on miniconda
python -m pip install pip-system-certs
python -c "import pip_system_certs.bootstrap"

make setup-models
make demo-live
```

Equivalent PowerShell:

```powershell
Get-Content .env | ForEach-Object { if ($_ -match '^\s*([^#][^=]+)=(.*)$') { Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim() } }
$env:PYTHONPATH = "packages/fre_core/src;."
python -m fre_core.cli demo --live --example all
```

Or: `.\scripts\dev.ps1 demo-live` after `.\scripts\dev.ps1 setup-models`.

## Validation outcome

- [x] Candidate `ReadinessReport` passes Pydantic + semantic validation
- [x] Evaluation metrics computed without manual reshaping
- [x] Generated LeanTask renders and typechecks (L1 `sorry` scaffold policy)

### Evaluation vs gold (`examples/finite_tree/`)

Live extraction output is written to `readiness_report.model.json` for inspection. ReadinessBench scoring in the demo still uses committed fixture predictions (`macro_f1_mean=1.0` on gold items).

After prompt tuning and `mathlib:` prefix normalization, live candidate strings should use Lean full names (e.g. `SimpleGraph.IsTree.card_edgeFinset`). Re-score live output manually when promoting artifacts.

## Dimension-level observations

### Existing theorem candidates

Extraction prompts now require mathlib dot-separated full names. Post-processing strips accidental `mathlib:` prefixes. The alignment step still surfaces `SimpleGraph.IsTree.card_edgeFinset` as the top candidate from the committed fixture readiness report during the post-extraction pipeline.

### LeanTask / formal target

L1 render uses `[Fintype G.edgeSet]` in binders (required for `G.edgeFinset.card`). `make demo-live` now passes Lean checks for both `finite_tree` and `category_theory_pullback` without `DEMO_SKIP_LEAN`.

## Error summary

| Category | Count | Notes |
|----------|-------|-------|
| Lean scaffold mismatch | 0 | Fixed via L1 binder updates |
| Windows OpenAI SSL | 0 | Documented `pip-system-certs` in `docs/DEMO.md` and `scripts/dev.ps1 setup-models` |

## Follow-ups

1. Promote improved live readiness reports to benchmark tiers only after human review.
2. Continue prompt tuning for constructive path / blocker phrasing if live-vs-gold F1 is needed for baselines.
