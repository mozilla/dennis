DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Available rules:"
	@fgrep -h "##" Makefile | fgrep -v fgrep | sed 's/\(.*\):.*##/\1:/'

.PHONY: clean
clean:  ## Clean build artifacts
	rm -rf build dist dennis.egg-info .tox
	rm -rf docs/_build/*
	find dennis/ tests/ -name __pycache__ | xargs rm -rf
	find dennis/ tests/ -name '*.pyc' | xargs rm -rf

.PHONY: lint
lint:  ## Lint and black reformat files
	black --target-version=py35 dennis tests
	flake8 dennis tests
