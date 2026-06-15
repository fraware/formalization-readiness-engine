# FRETasks Lean project

Pinned Lake project for checking LeanTask renderings from the Formalization Readiness Engine.

## Prerequisites

- [elan](https://github.com/leanprover/elan) (installs the Lean toolchain from `lean-toolchain`)
- Git (Lake fetches mathlib)

From the repository root, Python dependencies are required for `render-leantask` and `check-lean`:

```bash
make setup
```

On Windows without GNU Make:

```powershell
.\scripts\dev.ps1 setup
```

## Pinned versions

| Component | Pin |
|-----------|-----|
| Lean | `leanprover/lean4:v4.8.0` (`lean/lean-toolchain`) |
| mathlib4 | tag `v4.8.0` (`lean/lakefile.lean`) |

`lean/lake-manifest.json` is committed so `lake update` resolves the same dependency graph on every machine.

## Verification status

**Last verified:** 2026-06-14 at commit [`56e48e83`](https://github.com/fraware/formalization-readiness-engine/commit/56e48e83e760df24d35359ed230d934debadd094) (Windows, Lean 4.8.0, mathlib v4.8.0).

This commit records **Lean skeleton verification** only. The public release bundle cut (`f411fd5`) is documented separately in [`releases/v0.2.0/README.md`](../releases/v0.2.0/README.md); the two SHAs are not required to match.

| Check | Result |
|-------|--------|
| `lake build` | Pass |
| `FRETasks/Generated/FiniteTree.lean` | Pass (`sorry` warning) |
| `FRETasks/Generated/CategoryTheoryPullback.lean` | Pass (`sorry` warning) |

**What passes:** imports against pinned mathlib, statement signatures, and elaboration shape for both reference LeanTasks.

**What does not pass (by design):** proof completion. Generated L1 tasks use `sorry`; local `check-lean` and [`.github/workflows/lean.yml`](../.github/workflows/lean.yml) verify **syntax, imports, and typechecking scaffolding only** — not that informal statements are fully formalized or proof-checked.

Re-verify after changing generated tasks, renderer output, or Lean pins:

```bash
cd lean
lake update
lake exe cache get
lake build
lake env lean FRETasks/Generated/FiniteTree.lean
lake env lean FRETasks/Generated/CategoryTheoryPullback.lean
```

From the repository root, `python -m fre_core.cli check-lean … --project-dir lean` runs the same single-file checks used in CI.

## Setup

```bash
cd lean
lake update
lake exe cache get
lake build
```

`lake exe cache get` downloads precompiled mathlib artifacts. Run it after the first clone or whenever mathlib is updated; skipping it forces a long source build.

## Check a rendered LeanTask

Promote the finite-tree example to L1, render it, then typecheck through Lake:

```bash
python -m fre_core.cli render-leantask \
  examples/finite_tree/leantask_L1.json \
  lean/FRETasks/Generated/FiniteTree.lean

python -m fre_core.cli check-lean \
  lean/FRETasks/Generated/FiniteTree.lean \
  --project-dir lean
```

From the repository root you can also use:

```bash
make render-finite-tree-leantask
make check-lean-finite-tree
```

## L1 scaffold policy (`sorry`)

L1 LeanTask files are **statement scaffolds**: imports, binders, and the formal target must typecheck; the proof body may use `sorry`.

- `check-lean` runs `lake env lean` on a single file. Lean accepts `sorry` during typechecking, so scaffold checks pass without a completed proof.
- `lean/FRETasks/Examples/FiniteTree.lean` is a separate hand-reviewed alignment example with a real proof against pinned mathlib. It is built by `lake build` but is not the default `check-lean` target for rendered L1 output.
- L2 promotion (future) will require proof completion without `sorry` for gold-tier artifacts.

## Project layout

```text
lean/
  lean-toolchain          Lean version pin
  lakefile.lean           Lake package and mathlib pin
  lake-manifest.json      Locked dependency revisions (committed)
  FRETasks.lean           Root module
  FRETasks/
    Examples/             Hand-reviewed alignment targets
    Generated/            Renderer output (L1 scaffolds)
```

## CI

Normal Python CI does not build mathlib. [`.github/workflows/lean.yml`](../.github/workflows/lean.yml) builds the pinned project and runs `check-lean` on both generated reference tasks.

- **Manual:** `workflow_dispatch` on GitHub Actions (always available).
- **Automatic:** push or pull request that touches `lean/FRETasks/Generated/*.lean`, Lean project pins, or `packages/fre_core/src/fre_core/leantask*.py`.

The workflow checks the same `sorry`-based L1 scaffolds documented above; it does not gate proof completion.

The offline demo (`make demo`) renders and optionally typechecks L1 scaffolds for both reference examples. Python CI sets `DEMO_SKIP_LEAN=1` to skip Lean during automated runs.
