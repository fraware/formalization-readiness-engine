#!/usr/bin/env python3
"""Record live extraction evidence for v0.2 reference examples."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIVE_ROOT = REPO_ROOT / "artifacts" / "generated" / "demo_run" / "live"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "docs" / "evidence" / "live_extraction_v0.2"
BENCHMARK_ROOT = REPO_ROOT / "benchmarks" / "readinessbench"

EXAMPLES = (
    ("finite_tree", "finite_tree_edge_count"),
    ("category_theory_pullback", "category_theory_pullback_equivalence"),
)


def _ensure_path() -> None:
    src = REPO_ROOT / "packages" / "fre_core" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


ERROR_ANALYSIS_SECTIONS: dict[str, str] = {
    "finite_tree": """
## What worked

- **Existing-theorem alignment:** The model correctly surfaced `SimpleGraph.IsTree.card_edgeFinset`, matching the gold candidate. Lexical alignment in `alignment.json` also ranked this declaration first.
- **Statement and context dimensions:** Both were marked `clear` with faithful paraphrases of the finite-tree edge-count statement.
- **Proof strategy shape:** The constructive path lists the standard induction-on-vertices outline (leaf removal, inductive step, cardinality update).

## Error analysis

### False or weak candidates

- Alignment returned related theorems (`card_edgeFinset'`, neighboring `SimpleGraph` declarations) with lower scores. None were emitted as false positives in `existing_theorem_candidates`, but reviewers should watch substring matches on primed names.

### Blocker quality

- Predicted blockers focus on leaf-existence and deletion APIs. Gold blockers additionally require **definition alignment** (tree, leaf, `G-v`) and an explicit **reuse-vs-construct** decision. The model under-specified notation alignment (`G-v`) and the strategic fork between direct theorem reuse and constructive decomposition.

### Constructive path drift

- Gold path decomposes into five checkable obligations (leaf existence, deletion formalization, tree preservation, vertex-count update, edge-count update). The model collapsed these into fewer, less Mathlib-specific steps, yielding zero constructive-path F1 despite plausible prose.

### ProofGraph drift

- Generated graph uses free-form node types (`theorem`, `base_case`, `inductive_step`) rather than the gold scaffold (`theorem_statement`, `library_candidate`, `blocker`). Nodes are semantically reasonable but not comparable to the reviewed graph without normalization.

### Atlas record

- Live atlas used `blocker_type: definition-gap` (not in the gold controlled vocabulary `notation_alignment`). Evidence is source-grounded, but taxonomy alignment failed strict validation.

## Recommended follow-up

1. Promote constructive-path prompts toward Mathlib-named subgoals.
2. Constrain atlas `blocker_type` to the gold vocabulary during extraction post-processing.
3. Normalize ProofGraph node types before benchmark comparison.
""",
    "category_theory_pullback": """
## What worked

- **Statement recovery:** The model captured the pullback-stability statement under a categorical equivalence with accurate informal wording.
- **Dependency awareness:** Generated text references `CategoryTheory.Equivalence`, cones, and limit-preservation concepts appropriate to the domain.
- **Actionability:** `recommended_next_action` points to cone-category equivalence construction, which is a reasonable formalizer next step.

## Error analysis

### False candidates

- The model proposed `CategoryTheory.Limits.hasPullback_of_equivalence` and `CategoryTheory.Limits.isLimit.mapConeEquivalence`. Gold expert-reviewed candidates are `CategoryTheory.Equivalence.preservesLimitsOfShape` and `CategoryTheory.Limits.PreservesPullback`. Names differ entirely, yielding zero overlap F1 despite thematic relevance.

### Blocker quality

- Predicted blockers are high-level uncertainty statements ("uncertain if equivalence of cone categories exists"). Gold blockers enumerate concrete alignment gaps: equivalence vs isomorphism, unit/counit transport, reuse-vs-construct decision, and specific Mathlib module targets.

### Constructive path drift

- The model lists a four-step cone-transport proof sketch. Gold path aligns Mathlib `Equivalence`, imports limit-preservation, specializes to pullback shape, proves cone-category equivalence, and packages hypotheses. Step granularity and naming diverge completely from gold.

### Notation readiness

- Model notes generic pullback/cone notation gaps but misses gold-specific items: equivalence symbol vs `CategoryTheory.Equivalence`, and transport along diagram isomorphisms.

### ProofGraph drift

- Generated graph introduces `derived_fact`, `construction_step`, `application_step`, and duplicate `justification` nodes. Gold graph is smaller and uses `library_candidate` / `blocker` nodes tied to reviewed alignment decisions.

### Atlas record

- Live atlas used a long free-form `blocker_type` string unrelated to gold `notation_alignment`. Strict atlas validation fails; permissive validation passes on evidence text alone.

## Recommended follow-up

1. Add retrieval or few-shot examples that show gold Mathlib theorem names for category-theory limits.
2. Post-process theorem candidates against the fixture declaration index before reporting.
3. Tighten blocker prompts to emit taxonomy-aligned labels plus source spans.
""",
}


def _validation_passes(load_fn, path: Path, *, mode: str) -> bool:
    from fre_core.validation import ArtifactValidationError

    try:
        load_fn(path, mode=mode)
        return True
    except (ArtifactValidationError, ValueError):
        return False


def _validation_passes_normalized(load_fn, path: Path, filename: str) -> bool:
    from fre_core.artifact_normalization import normalize_atlas_record, normalize_proofgraph
    from fre_core.validation import ArtifactValidationError, validate_atlas_record, validate_proofgraph

    try:
        artifact = load_fn(path, mode="permissive")
        if filename == "proofgraph.model.json":
            validate_proofgraph(normalize_proofgraph(artifact), mode="public_export")
        elif filename == "atlas_record.model.json":
            validate_atlas_record(normalize_atlas_record(artifact), mode="public_export")
        else:
            load_fn(path, mode="public_export")
        return True
    except (ArtifactValidationError, ValueError):
        return False


def _validate_live_artifacts(example_key: str, live_root: Path) -> dict[str, dict[str, bool]]:
    from fre_core.validation import load_atlas_record, load_proofgraph, load_readiness_report

    example_dir = live_root / example_key
    checks: dict[str, dict[str, bool]] = {}
    artifact_loaders = {
        "readiness_report.model.json": load_readiness_report,
        "proofgraph.model.json": load_proofgraph,
        "atlas_record.model.json": load_atlas_record,
    }
    for filename, loader in artifact_loaders.items():
        path = example_dir / filename
        if not path.is_file():
            continue
        checks[filename] = {
            "strict": _validation_passes(loader, path, mode="strict"),
            "permissive": _validation_passes(loader, path, mode="permissive"),
            "public_export": _validation_passes_normalized(loader, path, filename),
        }
    return checks


def _write_error_analysis(
    *,
    output_root: Path,
    example_key: str,
    unit_id: str,
    live_root: Path,
    scores: dict[str, object],
    candidate_theorems: list[str],
    gold_theorems: list[str],
    validation: dict[str, dict[str, bool]],
) -> None:
    macro_f1 = scores.get("macro_f1")
    v03_metrics = scores.get("v03_metrics") or {}
    v03_macro = v03_metrics.get("v03_macro_f1")
    v03_theorem = v03_metrics.get("theorem_candidates_declaration_f1")
    analysis_path = output_root / f"{example_key}.md"
    gold_ref = f"benchmarks/readinessbench/gold/{unit_id}/"
    artifact_ref = live_root.relative_to(REPO_ROOT).as_posix()
    validation_lines = [
        f"- `{name}` strict: {'pass' if modes['strict'] else 'fail'}, "
        f"permissive: {'pass' if modes['permissive'] else 'fail'}, "
        f"public_export (normalized): {'pass' if modes.get('public_export') else 'fail'}"
        for name, modes in sorted(validation.items())
    ]
    narrative = ERROR_ANALYSIS_SECTIONS.get(example_key, "")
    content = f"""# Live extraction evidence — {example_key.replace('_', ' ')}

**Example:** `{example_key}` (`{unit_id}`)
**Source artifacts:** `{artifact_ref}/{example_key}/`
**Gold reference:** `{gold_ref}`

## Evaluation scores (ReadinessBench gold)

| Metric | Score |
|--------|------:|
| macro F1 (lexical v0.2) | {macro_f1} |
| existing theorem candidates F1 (lexical) | {scores.get('existing_theorem_candidates_f1')} |
| constructive path F1 | {scores.get('constructive_path_f1')} |
| blockers F1 | {scores.get('blockers_f1')} |
| notation readiness F1 | {scores.get('notation_readiness_f1')} |
| v0.3 macro F1 | {v03_macro} |
| theorem candidates F1 (declaration-ID v0.3) | {v03_theorem} |

## Validation (tiered)

Gold fixtures use strict validation; live candidate artifacts use permissive validation.
ProofGraph and Atlas public_export checks apply after artifact normalization.

{chr(10).join(validation_lines)}

## Theorem candidate comparison

- **Predicted:** {', '.join(candidate_theorems) or '(none)'}
- **Gold:** {', '.join(gold_theorems) or '(none)'}
{narrative}
"""
    analysis_path.write_text(content, encoding="utf-8")


def _score_example(
    *,
    example_key: str,
    unit_id: str,
    live_root: Path,
    output_root: Path,
) -> dict[str, object]:
    from fre_core.benchmark import run_benchmark_evaluation
    from fre_core.extraction import READINESS_EXTRACTION_INSTRUCTIONS
    from fre_core.validation import load_readiness_report

    prediction_path = live_root / example_key / "readiness_report.model.json"
    if not prediction_path.is_file():
        raise FileNotFoundError(f"Missing live prediction: {prediction_path}")

    with tempfile.TemporaryDirectory() as scratch_dir:
        scratch = Path(scratch_dir)
        manifest_path = scratch / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": "0.1",
                    "benchmark_id": "readinessbench",
                    "items": [
                        {
                            "item_id": f"{unit_id}_gold",
                            "unit_id": unit_id,
                            "tier": "gold",
                            "unit_path": f"gold/{unit_id}/unit.json",
                            "readiness_report_path": f"gold/{unit_id}/readiness_report.json",
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        predictions_dir = scratch / "predictions"
        unit_predictions = predictions_dir / unit_id
        unit_predictions.mkdir(parents=True, exist_ok=True)
        (unit_predictions / "readiness_report.json").write_text(
            prediction_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        for model_name, bench_name in (
            ("proofgraph.model.json", "proofgraph.json"),
            ("atlas_record.model.json", "atlas_record.json"),
        ):
            model_path = live_root / example_key / model_name
            if model_path.is_file():
                (unit_predictions / bench_name).write_text(
                    model_path.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
        report = run_benchmark_evaluation(
            manifest_path=manifest_path,
            predictions_dir=predictions_dir,
            benchmark_root=BENCHMARK_ROOT,
            repo_root=REPO_ROOT,
        )
    item = report.items[0]
    predicted = load_readiness_report(prediction_path, mode="permissive")
    gold_path = BENCHMARK_ROOT / "gold" / unit_id / "readiness_report.json"
    gold = load_readiness_report(gold_path)
    validation = _validate_live_artifacts(example_key, live_root)
    scores = {
        "macro_f1": item.macro_f1,
        "existing_theorem_candidates_f1": item.existing_theorem_candidates_f1,
        "constructive_path_f1": item.constructive_path_f1,
        "blockers_f1": item.blockers_f1,
        "notation_readiness_f1": item.notation_readiness_f1,
        "full_macro_f1": item.full_macro_f1,
        "v03_metrics": item.v03_metrics or {},
        "v03_macro_f1": report.v03_macro_f1_mean,
    }
    _write_error_analysis(
        output_root=output_root,
        example_key=example_key,
        unit_id=unit_id,
        live_root=live_root,
        scores=scores,
        candidate_theorems=predicted.existing_theorem_candidates,
        gold_theorems=gold.existing_theorem_candidates,
        validation=validation,
    )
    return {
        "example_key": example_key,
        "unit_id": unit_id,
        "prompt_version": hashlib.sha256(READINESS_EXTRACTION_INSTRUCTIONS.encode("utf-8")).hexdigest()[:12],
        "model_name": os.environ.get("FRE_MODEL_NAME", os.environ.get("OPENAI_MODEL", "gpt-4.1")),
        "prediction_path": prediction_path.relative_to(REPO_ROOT).as_posix(),
        "gold_path": gold_path.relative_to(REPO_ROOT).as_posix(),
        "validation": validation,
        "scores": scores,
        "candidate_theorems": predicted.existing_theorem_candidates,
        "gold_theorems": gold.existing_theorem_candidates,
        "artifact_checksums": {
            name: _sha256(live_root / example_key / name)
            for name in (
                "readiness_report.model.json",
                "readiness_report.enriched.json",
                "alignment.json",
                "proofgraph.model.json",
                "atlas_record.model.json",
                "leantask.model.json",
            )
            if (live_root / example_key / name).is_file()
        },
    }


def main() -> None:
    _ensure_path()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live-root",
        type=Path,
        default=DEFAULT_LIVE_ROOT,
        help="Directory containing live demo outputs per example key.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Directory for summary.json and per-example analysis markdown.",
    )
    args = parser.parse_args()
    live_root = args.live_root.resolve()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    entries = [
        _score_example(
            example_key=key,
            unit_id=unit_id,
            live_root=live_root,
            output_root=output_root,
        )
        for key, unit_id in EXAMPLES
    ]
    summary = {
        "schema_version": "0.1",
        "recorded_at": datetime.now(UTC).isoformat(),
        "live_root": live_root.relative_to(REPO_ROOT).as_posix(),
        "examples": entries,
    }
    (output_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {output_root / 'summary.json'}")


if __name__ == "__main__":
    main()
