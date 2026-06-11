from pathlib import Path

from fre_core.latex_ingestion import ingest_latex_file, parse_latex_theorem_blocks, theorem_blocks_to_units


LATEX_SOURCE = r"""
\section{Trees}

\begin{theorem}[Edges in a finite tree]
Let G be a finite tree. Then the number of edges is one less than the number of vertices.
\end{theorem}

\begin{proof}
Use induction on the number of vertices.
\end{proof}

\begin{lemma}
Every finite nontrivial tree has a leaf.
\end{lemma}
"""


def test_parse_latex_theorem_blocks_pairs_following_proof() -> None:
    blocks = parse_latex_theorem_blocks(LATEX_SOURCE)

    assert len(blocks) == 2
    assert blocks[0].env == "theorem"
    assert blocks[0].title == "Edges in a finite tree"
    assert "finite tree" in blocks[0].statement
    assert blocks[0].proof == "Use induction on the number of vertices."
    assert blocks[0].statement_span.start < blocks[0].statement_span.end
    assert blocks[0].proof_span is not None
    assert blocks[0].proof_span.start < blocks[0].proof_span.end


def test_parse_latex_theorem_blocks_allows_missing_proof() -> None:
    blocks = parse_latex_theorem_blocks(LATEX_SOURCE)

    assert blocks[1].env == "lemma"
    assert blocks[1].proof is None
    assert blocks[1].proof_span is None


def test_theorem_blocks_to_units_preserves_source_metadata() -> None:
    blocks = parse_latex_theorem_blocks(LATEX_SOURCE)
    units = theorem_blocks_to_units(blocks=blocks, source_id="source_001", domain="graph_theory")

    assert len(units) == 2
    assert units[0].unit_id == "source_001_0001_edges_in_a_finite_tree"
    assert units[0].source_id == "source_001"
    assert units[0].domain == "graph_theory"
    assert units[0].proof is not None


def test_ingest_latex_file(tmp_path: Path) -> None:
    source_path = tmp_path / "source.tex"
    source_path.write_text(LATEX_SOURCE, encoding="utf-8")

    units = ingest_latex_file(path=source_path, source_id="source_001", domain="graph_theory")

    assert len(units) == 2
    assert units[0].statement_span is not None
