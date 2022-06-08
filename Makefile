DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Available rules:"
	@fgrep -h "##" Makefile | fgrep -v fgrep | sed 's/\(.*\):.*##/\1:/'

.PHONY: clean
clean:  ## Clean build artifacts
	rm -rf build dist dennis.egg-info
	rm -rf docs/_build/*
	rm -rf _pytest_cache/ .tox
	find dennis/ tests/ -name __pycache__ | xargs rm -rf
	find dennis/ tests/ -name '*.pyc' | xargs rm -rf

.PHONY: lint
lint:  ## Lint and black reformat files
	black --target-version=py37 setup.py dennis tests
	flake8 dennis tests

.PHONY: test
test:  ## Run tests
	tox
