#!/usr/bin/env python3
"""Build committed embedding sidecars for mathlib declaration index fixtures.

Uses the deterministic hashed n-gram model in ``fre_core.embedding_index`` so
outputs are reproducible without network access or GPU dependencies. Run
offline when declaration fixtures change, then commit the generated JSON.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES = (
    REPO_ROOT / "fixtures" / "mathlib_declarations" / "finite_tree_v0.json",
    REPO_ROOT / "fixtures" / "mathlib_declarations" / "category_theory_v0.json",
)


def _ensure_path() -> None:
    src = REPO_ROOT / "packages" / "fre_core" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def build_sidecar(*, index_path: Path, output_path: Path | None = None) -> Path:
    _ensure_path()
    from fre_core.embedding_index import (
        build_declaration_embedding_sidecar,
        default_embedding_path,
        write_declaration_embedding_sidecar,
    )
    from fre_core.mathlib_index import load_index

    index = load_index(index_path)
    sidecar = build_declaration_embedding_sidecar(index=index)
    destination = output_path or default_embedding_path(index_path=index_path)
    write_declaration_embedding_sidecar(sidecar=sidecar, path=destination)
    print(f"wrote {len(sidecar.declarations)} vectors to {destination}")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "index_paths",
        nargs="*",
        type=Path,
        help="Declaration index fixture paths (default: finite_tree_v0 + category_theory_v0).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path (single index only). Defaults to *_embeddings.json beside the index.",
    )
    args = parser.parse_args()
    index_paths = args.index_paths or list(DEFAULT_FIXTURES)
    if args.output is not None and len(index_paths) != 1:
        parser.error("--output requires exactly one index path.")

    for index_path in index_paths:
        build_sidecar(index_path=index_path.resolve(), output_path=args.output)


if __name__ == "__main__":
    main()
