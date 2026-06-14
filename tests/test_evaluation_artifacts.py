from pathlib import Path

from fre_core.evaluation_atlas import score_atlas_record
from fre_core.evaluation_leantask import score_leantask_package
from fre_core.evaluation_proofgraph import score_proofgraph
from fre_core.validation import load_atlas_record, load_leantask_package, load_proofgraph

ROOT = Path(__file__).resolve().parents[1]


def test_score_proofgraph_on_finite_tree_example() -> None:
    gold_dir = ROOT / "examples" / "finite_tree"
    gold = load_proofgraph(gold_dir / "proofgraph.json")
    scores = score_proofgraph(predicted=gold, gold=gold)
    assert scores.macro_f1 == 1.0


def test_score_atlas_record_on_finite_tree_example() -> None:
    gold_dir = ROOT / "examples" / "finite_tree"
    gold = load_atlas_record(gold_dir / "atlas_record.json")
    scores = score_atlas_record(predicted=gold, gold=gold)
    assert scores.f1 == 1.0


def test_score_leantask_package_on_finite_tree_example() -> None:
    gold_dir = ROOT / "examples" / "finite_tree"
    gold = load_leantask_package(gold_dir / "leantask.json")
    scores = score_leantask_package(predicted=gold, gold=gold)
    assert scores.f1 == 1.0
