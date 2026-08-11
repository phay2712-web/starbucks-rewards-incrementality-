PYTHON ?= python3

.PHONY: all analysis figures notebook test clean

all: analysis figures notebook test

analysis:
	$(PYTHON) analysis/power.py
	$(PYTHON) analysis/economics.py
	$(PYTHON) analysis/simulate.py

figures:
	$(PYTHON) analysis/figures.py

notebook:
	$(PYTHON) scripts/execute_notebook.py

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

