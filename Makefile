PYTHON ?= python

.PHONY: setup test demo validate-examples lint

setup:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e packages/fre_core

test:
	PYTHONPATH=packages/fre_core/src pytest -q

validate-examples:
	PYTHONPATH=packages/fre_core/src $(PYTHON) -m fre_core.cli validate-unit examples/finite_tree/unit.json
	PYTHONPATH=packages/fre_core/src $(PYTHON) -m fre_core.cli validate-report examples/finite_tree/readiness_report.json

demo:
	PYTHONPATH=packages/fre_core/src $(PYTHON) -m fre_core.cli demo

lint:
	ruff check packages tests
