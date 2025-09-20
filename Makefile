# Makefile for nopal-detector

PYTHON ?= python3
VENV = .venv

.PHONY: setup run clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip wheel
	$(VENV)/bin/python -m pip install -r requirements.txt

run:
	$(VENV)/bin/python nopal_all_in_one.py --source 0 --ref data/ref/nopal_ref.jpg

clean:
	rm -rf $(VENV) __pycache__ */__pycache__ *.pyc *.pyo .pytest_cache .mypy_cache .coverage htmlcov
