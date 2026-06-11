PYTHON ?= python
PYTHONPATH_VALUE := packages/fre_core/src

.PHONY: setup setup-models test demo validate-examples export-schemas lint

setup:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e packages/fre_core

setup-models:
	$(PYTHON) -m pip install -r packages/fre_core/requirements-models.txt

test:
	PYTHONPATH=$(PYTHONPATH_VALUE) pytest -q

validate-examples:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli validate-example-dir examples/finite_tree

export-schemas:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli export-schemas schemas

demo:
	PYTHONPATH=$(PYTHONPATH_VALUE) $(PYTHON) -m fre_core.cli demo

lint:
	ruff check packages tests
