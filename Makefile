.DEFAULT_GOAL := help

.PHONY: help install dev test test-file test-dir inspect

help:
	@printf '%s\n' 'Targets: install, dev, test, test-file FILE=..., test-dir DIR=..., inspect FILE=...'

install:
	python -m pip install -e .

dev:
	python -m pip install -e ".[dev]"

test:
	python -m pytest -q

test-file:
	python -m pytest -q $(FILE)

test-dir:
	python -m pytest -q $(DIR)

inspect:
	sdi inspect $(FILE)
