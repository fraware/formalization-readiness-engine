# Engineering branch status

Historical record for the June 2026 public release. All engineering work described below is merged on `main`.

## Current state

`main` includes Waves 0–6, Docker/RQ infrastructure, ReadinessBench v0.2.0 scale-up, and both reference examples. Temporary `engineering-*` branches were squash-merged and deleted from the remote after consolidation.

There are no active engineering sprint branches. New work should branch from `main`.

## What was merged

The following capabilities arrived through a linear stack of short-lived branches, consolidated before public release:

| Capability | Summary |
|------------|---------|
| Readiness harness | Live extraction loop, evaluation metrics, baseline notes template |
| Pinned Lean | Lean v4.8.0 + mathlib pin, `lake-manifest.json`, Generated scaffolds |
| Corpus catalog | Catalog ingestion, shareable export, release-mode filtering |
| ProofGraph and Atlas extraction | Model-assisted extraction with post-extraction semantic validation |
| mathlib index v0 | Declaration index fixtures and lexical lookup |
| ReadinessBench tiers | Bronze/Silver/Gold layout, manifest validation, evaluation runner |
| External review | Reviewer docs, submission template, Gold changelog |
| Category-theory example | Second hand-authored reference stack |
| LeanTask generation | Model-assisted LeanTask packages from readiness reports |
| Phase 5–6 | Alignment service, review API/UI, public export, licensing leak tests |
| E2E demo | Offline and live demos for both reference examples |
| Wave 1–6 scale-up | Corpus expansion (30 units), gold benchmark growth (11 items), Docker/RQ jobs |

## Branch cleanup

Merged engineering branches were removed from GitHub after confirmation that `main` contained their commits. See `docs/BRANCH_CLEANUP.md` for the completed cleanup record.

## For new contributors

Do not look for `engineering-sprint*` branches. Start from `main`, read `docs/ENGINEERING_HANDOFF.md`, and consult `docs/NEXT_SPRINTS.md` for optional follow-on work.
