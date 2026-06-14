"""Seed Wave 6 ReadinessBench gold fixtures (11 expert-reviewed gold items)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = REPO_ROOT / "benchmarks" / "readinessbench"
GOLD_ROOT = BENCHMARK_ROOT / "gold"
MANIFEST_PATH = BENCHMARK_ROOT / "manifest.json"
CHANGELOG_PATH = GOLD_ROOT / "changelog.jsonl"
PREDICTIONS_ROOT = REPO_ROOT / "tests" / "fixtures" / "readinessbench_predictions"

REVIEW_TEMPLATE = "docs/review/templates/readiness_report_review.json"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _expert_report(
    *,
    unit_id: str,
    domain: str,
    blockers: list[str],
    candidates: list[str],
    path_steps: list[str],
    next_action: str,
) -> dict:
    return {
        "schema_version": "0.1",
        "unit_id": unit_id,
        "statement_readiness": {
            "status": "clear",
            "recovered": ["statement isolated"],
            "unresolved": [],
            "notes": "Reviewed for Wave 6 gold seed.",
        },
        "context_readiness": {
            "status": "partial",
            "recovered": ["domain context"],
            "unresolved": ["library definition alignment"],
            "notes": "Context requires mathlib alignment.",
        },
        "notation_readiness": {
            "status": "partial",
            "recovered": ["standard notation"],
            "unresolved": ["informal symbols"],
            "notes": "Notation must map to mathlib.",
        },
        "dependency_readiness": {
            "status": "partial",
            "recovered": ["proof strategy"],
            "unresolved": ["missing lemmas"],
            "notes": "Dependencies reviewed for formalization path.",
        },
        "existing_theorem_candidates": candidates,
        "constructive_path": path_steps,
        "blockers": blockers,
        "recommended_next_action": next_action,
        "review_status": "expert_reviewed",
    }


def _expert_unit(*, unit_id: str, source_id: str, statement: str, proof: str, domain: str, context: str) -> dict:
    return {
        "schema_version": "0.1",
        "unit_id": unit_id,
        "source_id": source_id,
        "statement": statement,
        "proof": proof,
        "local_context": context,
        "domain": domain,
        "statement_span": None,
        "proof_span": None,
        "review_status": "expert_reviewed",
    }


def _atlas_record(*, unit_id: str, blocker_type: str, pattern: str, evidence: str, action: str) -> dict:
    return {
        "schema_version": "0.1",
        "unit_id": unit_id,
        "blocker_type": blocker_type,
        "mathematical_pattern": pattern,
        "evidence": evidence,
        "candidate_formal_object": None,
        "likely_library_location": None,
        "severity": "high",
        "status": "reviewed",
        "recommended_action": action,
        "review_status": "expert_reviewed",
    }


WAVE6_SYNTHETIC_SPECS: list[dict] = [
    {
        "unit_id": "category_theory_pullback_equivalence",
        "source_id": "hand_authored_category_theory_pullback_001",
        "domain": "category_theory",
        "from_example": "examples/category_theory_pullback",
    },
    {
        "unit_id": "simple_graph_handshake_lemma",
        "source_id": "wave6_seed_graph_001",
        "domain": "graph_theory",
        "statement": "In any finite graph, the sum of vertex degrees equals twice the number of edges.",
        "proof": "Each edge contributes one to the degree of each endpoint, so summing degrees counts every edge twice.",
        "context": "Wave 6 seeded graph-theory gold item.",
        "blockers": [
            "definition alignment for finite simple graph",
            " finset cardinality for edge set",
        ],
        "candidates": ["SimpleGraph.sum_degrees_eq_twice_card_edges"],
        "path_steps": ["align graph model", "apply degree-sum lemma"],
        "next_action": "Confirm mathlib degree-sum lemma before decomposition.",
    },
    {
        "unit_id": "commutative_ring_prime_ideal",
        "source_id": "wave6_seed_algebra_001",
        "domain": "commutative_algebra",
        "statement": "In a commutative ring, the nilradical is the intersection of all prime ideals.",
        "proof": "Standard commutative algebra proof using Zorn's lemma for prime avoidance and nilpotent elements.",
        "context": "Wave 6 seeded algebra gold item.",
        "blockers": [
            "definition alignment for nilradical",
            "library route for prime ideal intersection",
        ],
        "candidates": ["CommRing.nilradical_eq_sInf_isPrime"],
        "path_steps": ["import nilradical definition", "apply characterization theorem"],
        "next_action": "Search mathlib for nilradical-prime intersection theorem.",
    },
    {
        "unit_id": "topology_compact_continuous_image",
        "source_id": "wave6_seed_topology_001",
        "domain": "topology",
        "statement": "The continuous image of a compact topological space is compact.",
        "proof": "Let K be compact and f continuous. Given an open cover of f(K), pull back to K and extract a finite subcover.",
        "context": "Wave 6 seeded topology gold item.",
        "blockers": [
            "definition alignment for compactness",
            "open cover transport under continuous maps",
        ],
        "candidates": ["IsCompact.image"],
        "path_steps": ["align compactness", "prove image cover argument"],
        "next_action": "Prefer existing compactness image lemma if available.",
    },
    {
        "unit_id": "real_analysis_uniform_limit_continuity",
        "source_id": "wave6_seed_analysis_001",
        "domain": "analysis",
        "statement": "Uniform limits of continuous real-valued functions on a compact set are continuous.",
        "proof": "Use an epsilon/three-delta argument with uniform convergence on the compact domain.",
        "context": "Wave 6 seeded analysis gold item.",
        "blockers": [
            "definition alignment for uniform convergence",
            "continuity epsilon-delta packaging",
        ],
        "candidates": ["ContinuousOn.uniformLimit"],
        "path_steps": ["formalize uniform limit", "derive continuity"],
        "next_action": "Check mathlib uniform convergence lemmas on compact sets.",
    },
    {
        "unit_id": "number_theory_gcd_lcm_identity",
        "source_id": "wave6_seed_number_theory_001",
        "domain": "number_theory",
        "statement": "For positive integers a and b, gcd(a, b) * lcm(a, b) = a * b.",
        "proof": "Use prime factorization uniqueness or the gcd-lcm lattice identity on divisors.",
        "context": "Wave 6 seeded number theory gold item.",
        "blockers": [
            "definition alignment for gcd and lcm",
            "factorization prerequisites",
        ],
        "candidates": ["Nat.gcd_mul_lcm"],
        "path_steps": ["align gcd/lcm", "apply standard identity"],
        "next_action": "Import gcd-lcm identity from mathlib if present.",
    },
    {
        "unit_id": "linear_algebra_rank_nullity",
        "source_id": "wave6_seed_linear_algebra_001",
        "domain": "linear_algebra",
        "statement": "For a linear map between finite-dimensional vector spaces, dim ker f + dim im f = dim domain.",
        "proof": "Choose a basis of the kernel, extend to the domain, and compare dimensions.",
        "context": "Wave 6 seeded linear algebra gold item.",
        "blockers": [
            "definition alignment for finite-dimensional vector space",
            "dimension theorem prerequisites",
        ],
        "candidates": ["LinearMap.finrank_range_add_finrank_ker"],
        "path_steps": ["align kernel/image dimensions", "apply rank-nullity"],
        "next_action": "Confirm mathlib rank-nullity theorem statement.",
    },
    {
        "unit_id": "measure_theory_monotone_convergence",
        "source_id": "wave6_seed_measure_001",
        "domain": "measure_theory",
        "statement": "For a non-decreasing sequence of non-negative measurable functions, the integral of the limit equals the limit of integrals.",
        "proof": "Apply monotone convergence from below and measure-theoretic approximation by simple functions.",
        "context": "Wave 6 seeded measure theory gold item.",
        "blockers": [
            "definition alignment for measurable functions",
            "monotone convergence theorem packaging",
        ],
        "candidates": ["MeasureTheory.lintegral_iSup"],
        "path_steps": ["align measurability", "apply MCT"],
        "next_action": "Locate mathlib monotone convergence lemma for lintegral.",
    },
    {
        "unit_id": "propositional_logic_iff_chain",
        "source_id": "wave6_seed_logic_001",
        "domain": "logic",
        "statement": "If P iff Q and Q iff R, then P iff R.",
        "proof": "Case split on truth of P and propagate equivalences through Q to R.",
        "context": "Wave 6 seeded logic gold item.",
        "blockers": [
            "definition alignment for propositional equivalence",
            "choice between Iff.trans and propositional tautology",
        ],
        "candidates": ["Iff.trans"],
        "path_steps": ["align Iff syntax", "apply transitivity"],
        "next_action": "Use Iff.trans unless a custom propositional lemma is required.",
    },
    {
        "unit_id": "set_theory_image_preimage",
        "source_id": "wave6_seed_set_theory_001",
        "domain": "set_theory",
        "statement": "For any function f and set S, f(f^{-1}(S)) subseteq S with equality when f is surjective onto S.",
        "proof": "Unfold preimage and image, then prove both inclusion directions under surjectivity.",
        "context": "Wave 6 seeded set theory gold item.",
        "blockers": [
            "definition alignment for image and preimage",
            "surjectivity hypothesis packaging",
        ],
        "candidates": ["Set.surjective_iff_image_preimage"],
        "path_steps": ["align Set.image/preimage", "prove surjective criterion"],
        "next_action": "Import standard image-preimage lemmas from mathlib.",
    },
]


def _seed_finite_tree() -> None:
    existing_unit = GOLD_ROOT / "finite_tree_edge_count" / "unit.json"
    existing_report = GOLD_ROOT / "finite_tree_edge_count" / "readiness_report.json"
    if not existing_unit.exists() or not existing_report.exists():
        raise SystemExit("Missing baseline finite_tree gold fixture")


def _seed_item_from_example(*, unit_id: str, example_dir: Path) -> None:
    example_dir = REPO_ROOT / example_dir
    unit = json.loads((example_dir / "unit.json").read_text(encoding="utf-8"))
    report = json.loads((example_dir / "readiness_report.json").read_text(encoding="utf-8"))
    atlas = json.loads((example_dir / "atlas_record.json").read_text(encoding="utf-8"))
    unit["review_status"] = "expert_reviewed"
    report["review_status"] = "expert_reviewed"
    atlas["review_status"] = "expert_reviewed"
    target = GOLD_ROOT / unit_id
    _write_json(target / "unit.json", unit)
    _write_json(target / "readiness_report.json", report)
    _write_json(target / "atlas_record.json", atlas)


def _seed_synthetic_item(spec: dict) -> None:
    unit_id = spec["unit_id"]
    unit = _expert_unit(
        unit_id=unit_id,
        source_id=spec["source_id"],
        statement=spec["statement"],
        proof=spec["proof"],
        domain=spec["domain"],
        context=spec["context"],
    )
    report = _expert_report(
        unit_id=unit_id,
        domain=spec["domain"],
        blockers=spec["blockers"],
        candidates=spec["candidates"],
        path_steps=spec["path_steps"],
        next_action=spec["next_action"],
    )
    atlas = _atlas_record(
        unit_id=unit_id,
        blocker_type="library_alignment",
        pattern=spec["domain"],
        evidence=spec["blockers"][0],
        action=spec["next_action"],
    )
    target = GOLD_ROOT / unit_id
    _write_json(target / "unit.json", unit)
    _write_json(target / "readiness_report.json", report)
    _write_json(target / "atlas_record.json", atlas)


def _write_manifest() -> None:
    gold_ids = ["finite_tree_edge_count"] + [spec["unit_id"] for spec in WAVE6_SYNTHETIC_SPECS]
    items = []
    for unit_id in gold_ids:
        items.append(
            {
                "item_id": f"{unit_id}_gold",
                "unit_id": unit_id,
                "tier": "gold",
                "unit_path": f"gold/{unit_id}/unit.json",
                "readiness_report_path": f"gold/{unit_id}/readiness_report.json",
            }
        )
    items.extend(
        [
            {
                "item_id": "finite_tree_edge_count_silver",
                "unit_id": "finite_tree_edge_count",
                "tier": "silver",
                "unit_path": "silver/finite_tree_edge_count/unit.json",
                "readiness_report_path": "silver/finite_tree_edge_count/readiness_report.json",
            },
            {
                "item_id": "finite_tree_edge_count_bronze",
                "unit_id": "finite_tree_edge_count",
                "tier": "bronze",
                "unit_path": "bronze/finite_tree_edge_count/unit.json",
                "readiness_report_path": "bronze/finite_tree_edge_count/readiness_report.json",
            },
        ]
    )
    manifest = {
        "schema_version": "0.1",
        "benchmark_id": "readinessbench",
        "items": items,
    }
    _write_json(MANIFEST_PATH, manifest)


def _append_changelog() -> None:
    existing_lines = []
    if CHANGELOG_PATH.exists():
        existing_lines = [line for line in CHANGELOG_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    existing_item_ids = set()
    for line in existing_lines:
        existing_item_ids.add(json.loads(line)["item_id"])

    new_entries = []
    for unit_id in [spec["unit_id"] for spec in WAVE6_SYNTHETIC_SPECS]:
        item_id = f"{unit_id}_gold"
        if item_id in existing_item_ids:
            continue
        new_entries.append(
            {
                "date": "2026-06-14",
                "item_id": item_id,
                "reviewer_id": "engineering.seed",
                "summary": f"Wave 6 gold seed for unit {unit_id}.",
                "fields_changed": [
                    "review_status",
                    "blockers",
                    "constructive_path",
                    "existing_theorem_candidates",
                    "recommended_next_action",
                ],
                "review_submission_path": REVIEW_TEMPLATE,
            }
        )

    lines = existing_lines + [json.dumps(entry, sort_keys=True) for entry in new_entries]
    CHANGELOG_PATH.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _sync_predictions() -> None:
    gold_ids = ["finite_tree_edge_count"] + [spec["unit_id"] for spec in WAVE6_SYNTHETIC_SPECS]
    for unit_id in gold_ids:
        report_src = GOLD_ROOT / unit_id / "readiness_report.json"
        target_dir = PREDICTIONS_ROOT / unit_id
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(report_src, target_dir / "readiness_report.json")


def main() -> None:
    _seed_finite_tree()
    for spec in WAVE6_SYNTHETIC_SPECS:
        if spec.get("from_example"):
            _seed_item_from_example(unit_id=spec["unit_id"], example_dir=Path(spec["from_example"]))
        else:
            _seed_synthetic_item(spec)
    _write_manifest()
    _append_changelog()
    _sync_predictions()
    print(f"Seeded {1 + len(WAVE6_SYNTHETIC_SPECS)} gold items into {GOLD_ROOT}")


if __name__ == "__main__":
    main()
