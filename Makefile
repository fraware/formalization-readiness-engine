PYTHON ?= python
PYTHONPATH_VALUE := packages/fre_core/src:.

.PHONY: setup setup-models docs setup-api test demo demo-live demo-finite-tree demo-category-theory \
	validate-examples export-schemas lint check setup-lean build-lean \
	render-finite-tree-leantask check-lean-finite-tree validate-corpus-catalog ingest-catalog \
	extract-finite-tree-proofgraph extract-finite-tree-atlas lookup-finite-tree-declarations \
	generate-finite-tree-leantask generate-category-theory-leantask \
	validate-readinessbench run-readinessbench validate-review-submission validate-gold-changelog \
	run-api run-review-ui export-public-benchmark export-public-atlas

PREDICTIONS_DIR ?= tests/fixtures/readinessbench_predictions


docs:
	$(PYTHON) -m pip install -r requirements-docs.txt
	$(PYTHON) -m mkdocs build -f apps/docs-site/mkdocs.yml

setup:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e packages/fre_core

setup-models:
	$(PYTHON) -m pip install -r packages/fre_core/requirements-models.txt

setup-api:
	$(PYTHON) -m pip install -r requirements-api.txt

test:
	PYTHONPATH=$(PYTHONPATH_VALUE) pytest -q

validate-examples:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli validate-example-dir examples/finite_tree
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli validate-example-dir examples/category_theory_pullback

export-schemas:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli export-schemas schemas

demo:
	DEMO_SKIP_LEAN=1 PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli demo --offline --example all

demo-live:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli demo --live --example all

demo-finite-tree:
	DEMO_SKIP_LEAN=1 PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli demo --offline --example finite_tree

demo-category-theory:
	DEMO_SKIP_LEAN=1 PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli demo --offline --example category_theory_pullback

validate-corpus-catalog:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli validate-corpus-catalog corpus/catalog.json --repo-root .

ingest-catalog:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli ingest-catalog corpus/catalog.json corpus/units --repo-root .

ingest-corpus:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli ingest-catalog examples/corpus_shareable/catalog.json examples/corpus_shareable/ingested --repo-root .

export-corpus-shareable: ingest-corpus
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli export-shareable-units \
		examples/corpus_shareable/ingested \
		examples/corpus_shareable/catalog.json \
		examples/corpus_shareable/full_text_export \
		--include-text
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli export-shareable-units \
		examples/corpus_shareable/ingested \
		examples/corpus_shareable/catalog.json \
		examples/corpus_shareable/metadata_only_export

lint:
	ruff check packages tests apps

setup-lean:
	cd lean && lake update && lake exe cache get

build-lean:
	cd lean && lake build

render-finite-tree-leantask:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli render-leantask \
		examples/finite_tree/leantask_L1.json \
		lean/FRETasks/Generated/FiniteTree.lean

check-lean-finite-tree:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli check-lean \
		lean/FRETasks/Generated/FiniteTree.lean \
		--project-dir lean \
		--timeout-seconds 300

check: test validate-examples lint

extract-finite-tree-proofgraph:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli extract-proofgraph \
		examples/finite_tree/unit.json \
		artifacts/generated/finite_tree/proofgraph.model.json

extract-finite-tree-atlas:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli extract-atlas \
		examples/finite_tree/unit.json \
		artifacts/generated/finite_tree/atlas_record.model.json

lookup-finite-tree-declarations:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli lookup-declarations \
		--unit-path examples/finite_tree/unit.json

generate-finite-tree-leantask:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli generate-leantask \
		examples/finite_tree/unit.json \
		examples/finite_tree/readiness_report.json \
		artifacts/generated/finite_tree/leantask.model.json

generate-category-theory-leantask:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli generate-leantask \
		examples/category_theory_pullback/unit.json \
		examples/category_theory_pullback/readiness_report.json \
		artifacts/generated/category_theory_pullback/leantask.model.json

validate-readinessbench:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli validate-readinessbench

run-readinessbench:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli run-readinessbench \
		$(PREDICTIONS_DIR)

validate-review-submission:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli validate-review-submission \
		docs/review/templates/readiness_report_review.json

validate-gold-changelog:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli validate-gold-changelog

run-api:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000

run-review-ui:
	cd apps/review-ui && $(PYTHON) -m http.server 8080

export-public-benchmark:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli export-public-benchmark

export-public-atlas:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli export-public-atlas
