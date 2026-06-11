PYTHON ?= python

.PHONY: setup setup-models test demo validate-examples lint

setup:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e packages/fre_core

setup-models:
	$(PYTHON) -m pip install -r packages/fre_core/requirements-models.txt

test:
	PYTHONPATH=packages/fre_core/src pytest -q

validate-examples:
	PYTHONPATH=packages/fre_core/src $(PYTHON) -m fre_core.cli validate-example-dir examples/finite_tree

demo:
	PYTHONPATH=packages/fre_core/src $(PYTHON) -m fre_core.cli demo

lint:
	ruff check packages tests
