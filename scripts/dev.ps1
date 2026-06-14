# Windows development helpers when GNU Make is unavailable.
# Usage: .\scripts\dev.ps1 test

param(
    [Parameter(Position = 0)]
    [ValidateSet("setup", "setup-models", "setup-api", "test", "demo", "demo-live", "demo-finite-tree", "demo-category-theory", "validate-examples", "export-schemas", "lint", "check", "setup-lean", "build-lean", "render-finite-tree-leantask", "check-lean-finite-tree", "ingest-corpus", "export-corpus-shareable", "extract-finite-tree-proofgraph", "extract-finite-tree-atlas", "lookup-finite-tree-declarations", "generate-finite-tree-leantask", "generate-category-theory-leantask", "validate-readinessbench", "run-readinessbench", "validate-review-submission", "validate-gold-changelog", "run-api", "run-review-ui", "export-public-benchmark", "export-public-atlas")]
    [string]$Command = "test",
    [string]$PredictionsDir = "tests/fixtures/readinessbench_predictions"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$env:PYTHONPATH = "packages/fre_core/src;."

function Invoke-Setup {
    python -m pip install -r requirements.txt
    python -m pip install -e packages/fre_core
}

function Invoke-SetupModels {
    python -m pip install -r packages/fre_core/requirements-models.txt
}

function Invoke-SetupApi {
    python -m pip install -r requirements-api.txt
}

switch ($Command) {
    "setup" { Invoke-Setup }
    "setup-models" { Invoke-SetupModels }
    "setup-api" { Invoke-SetupApi }
    "test" { python -m pytest -q }
    "demo" {
        $env:DEMO_SKIP_LEAN = "1"
        python -m fre_core.cli demo --offline --example all
    }
    "demo-live" {
        python -m fre_core.cli demo --live --example all
    }
    "demo-finite-tree" {
        $env:DEMO_SKIP_LEAN = "1"
        python -m fre_core.cli demo --offline --example finite_tree
    }
    "demo-category-theory" {
        $env:DEMO_SKIP_LEAN = "1"
        python -m fre_core.cli demo --offline --example category_theory_pullback
    }
    "validate-examples" {
        python -m fre_core.cli validate-example-dir examples/finite_tree
        python -m fre_core.cli validate-example-dir examples/category_theory_pullback
    }
    "export-schemas" {
        python -m fre_core.cli export-schemas schemas
    }
    "lint" {
        ruff check packages tests apps
    }
    "setup-lean" {
        Push-Location lean
        try {
            lake update
            lake exe cache get
        } finally {
            Pop-Location
        }
    }
    "build-lean" {
        Push-Location lean
        try {
            lake build
        } finally {
            Pop-Location
        }
    }
    "render-finite-tree-leantask" {
        python -m fre_core.cli render-leantask `
            examples/finite_tree/leantask_L1.json `
            lean/FRETasks/Generated/FiniteTree.lean
    }
    "check-lean-finite-tree" {
        python -m fre_core.cli check-lean `
            lean/FRETasks/Generated/FiniteTree.lean `
            --project-dir lean `
            --timeout-seconds 300
    }
    "check" {
        python -m pytest -q
        python -m fre_core.cli validate-example-dir examples/finite_tree
        python -m fre_core.cli validate-example-dir examples/category_theory_pullback
        ruff check packages tests apps
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
    "lookup-finite-tree-declarations" {
        python -m fre_core.cli lookup-declarations `
            --unit-path examples/finite_tree/unit.json
    }
    "generate-finite-tree-leantask" {
        python -m fre_core.cli generate-leantask `
            examples/finite_tree/unit.json `
            examples/finite_tree/readiness_report.json `
            artifacts/generated/finite_tree/leantask.model.json
    }
    "generate-category-theory-leantask" {
        python -m fre_core.cli generate-leantask `
            examples/category_theory_pullback/unit.json `
            examples/category_theory_pullback/readiness_report.json `
            artifacts/generated/category_theory_pullback/leantask.model.json
    }
    "validate-readinessbench" {
        python -m fre_core.cli validate-readinessbench
    }
    "run-readinessbench" {
        python -m fre_core.cli run-readinessbench $PredictionsDir
    }
    "validate-review-submission" {
        python -m fre_core.cli validate-review-submission `
            docs/review/templates/readiness_report_review.json
    }
    "validate-gold-changelog" {
        python -m fre_core.cli validate-gold-changelog
    }
    "run-api" {
        python -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
    }
    "run-review-ui" {
        Push-Location apps/review-ui
        try {
            python -m http.server 8080
        } finally {
            Pop-Location
        }
    }
    "export-public-benchmark" {
        python -m fre_core.cli export-public-benchmark
    }
    "export-public-atlas" {
        python -m fre_core.cli export-public-atlas
    }
}
