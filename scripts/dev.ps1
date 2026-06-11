# Windows development helpers when GNU Make is unavailable.
# Usage: .\scripts\dev.ps1 test

param(
    [Parameter(Position = 0)]
    [ValidateSet("setup", "setup-models", "test", "validate-examples", "export-schemas", "lint", "check", "ingest-corpus", "export-corpus-shareable", "extract-finite-tree-proofgraph", "extract-finite-tree-atlas")]
    [string]$Command = "test"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$env:PYTHONPATH = "packages/fre_core/src"

function Invoke-Setup {
    python -m pip install -r requirements.txt
    python -m pip install -e packages/fre_core
}

function Invoke-SetupModels {
    python -m pip install -r packages/fre_core/requirements-models.txt
}

switch ($Command) {
    "setup" { Invoke-Setup }
    "setup-models" { Invoke-SetupModels }
    "test" { python -m pytest -q }
    "validate-examples" {
        python -m fre_core.cli validate-example-dir examples/finite_tree
    }
    "export-schemas" {
        python -m fre_core.cli export-schemas schemas
    }
    "lint" {
        ruff check packages tests
    }
    "check" {
        python -m pytest -q
        python -m fre_core.cli validate-example-dir examples/finite_tree
        ruff check packages tests
    }
    "ingest-corpus" {
        python -m fre_core.cli ingest-catalog `
            examples/corpus_shareable/catalog.json `
            examples/corpus_shareable/ingested `
            --repo-root .
    }
    "export-corpus-shareable" {
        python -m fre_core.cli ingest-catalog `
            examples/corpus_shareable/catalog.json `
            examples/corpus_shareable/ingested `
            --repo-root .
        python -m fre_core.cli export-shareable-units `
            examples/corpus_shareable/ingested `
            examples/corpus_shareable/catalog.json `
            examples/corpus_shareable/full_text_export `
            --include-text
        python -m fre_core.cli export-shareable-units `
            examples/corpus_shareable/ingested `
            examples/corpus_shareable/catalog.json `
            examples/corpus_shareable/metadata_only_export
    }
    "extract-finite-tree-proofgraph" {
        python -m fre_core.cli extract-proofgraph `
            examples/finite_tree/unit.json `
            artifacts/generated/finite_tree/proofgraph.model.json
    }
    "extract-finite-tree-atlas" {
        python -m fre_core.cli extract-atlas `
            examples/finite_tree/unit.json `
            artifacts/generated/finite_tree/atlas_record.model.json
    }
}
