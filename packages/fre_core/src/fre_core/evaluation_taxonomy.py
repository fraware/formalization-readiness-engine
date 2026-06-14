"""Baseline error taxonomy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from fre_core.evaluation import score_readiness_report
from fre_core.evaluation_proofgraph import score_proofgraph
from fre_core.validation import load_proofgraph, load_readiness_report


class ErrorCategory(str, Enum):
    NOTATION = "notation"
    BLOCKERS = "blockers"
    WRONG_CANDIDATES = "wrong_candidates"
    CONSTRUCTIVE_PATH = "constructive_path"
    PROOFGRAPH_NODES = "proofgraph_nodes"
    PROOFGRAPH_EDGES = "proofgraph_edges"
    ATLAS_EVIDENCE = "atlas_evidence"
    ATLAS_BLOCKER_TYPE = "atlas_blocker_type"
    ATLAS_RECOMMENDED_ACTION = "atlas_recommended_action"
    LEANTASK_IMPORTS = "leantask_imports"
    LEANTASK_HYPOTHESES = "leantask_hypotheses"
    LEANTASK_FORMAL_TARGET = "leantask_formal_target"


@dataclass(frozen=True)
class BaselineErrorSummary:
    unit_id: str
    categories: list[ErrorCategory]


def categorize_baseline_run(*, predicted_dir: Path, gold_dir: Path, unit_id: str) -> BaselineErrorSummary:
    categories: list[ErrorCategory] = []
    predicted_report = predicted_dir / "readiness_report.json"
    gold_report = gold_dir / "readiness_report.json"
    if predicted_report.is_file() and gold_report.is_file():
        scores = score_readiness_report(
            predicted=load_readiness_report(predicted_report),
            gold=load_readiness_report(gold_report),
        )
        if scores.notation_readiness.f1 < 1.0:
            categories.append(ErrorCategory.NOTATION)
        if scores.blockers.f1 < 1.0:
            categories.append(ErrorCategory.BLOCKERS)
        if scores.existing_theorem_candidates.f1 < 1.0:
            categories.append(ErrorCategory.WRONG_CANDIDATES)
        if scores.constructive_path.f1 < 1.0:
            categories.append(ErrorCategory.CONSTRUCTIVE_PATH)

    predicted_graph = predicted_dir / "proofgraph.json"
    gold_graph = gold_dir / "proofgraph.json"
    if predicted_graph.is_file() and gold_graph.is_file():
        graph_scores = score_proofgraph(
            predicted=load_proofgraph(predicted_graph),
            gold=load_proofgraph(gold_graph),
        )
        if graph_scores.nodes.f1 < 1.0:
            categories.append(ErrorCategory.PROOFGRAPH_NODES)
        if graph_scores.edges.f1 < 1.0:
            categories.append(ErrorCategory.PROOFGRAPH_EDGES)

    return BaselineErrorSummary(unit_id=unit_id, categories=categories)


def aggregate_error_summaries(*, summaries: list[BaselineErrorSummary]) -> dict[str, object]:
    counts = {category.value: 0 for category in ErrorCategory}
    for summary in summaries:
        for category in summary.categories:
            counts[category.value] += 1
    unit_count = len(summaries)
    return {
        "schema_version": "0.1",
        "unit_count": unit_count,
        "total_errors": sum(counts.values()),
        "categories": {
            key: {"count": value, "rate": round(value / unit_count, 6) if unit_count else 0.0}
            for key, value in counts.items()
        },
    }
