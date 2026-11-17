.DEFAULT_GOAL := help

POETRY ?= poetry
OUT ?= .
FORMAT ?=

.PHONY: help poetry install test inspect ui build

help:
	@echo "make poetry     install Poetry if it is missing"
	@echo "make install    install the project with dev and UI extras"
	@echo "make test       run the tests (pass ARGS=... for pytest options)"
	@echo "make inspect FILE=data.csv [OUT=dir|report.md] [FORMAT=markdown|json|both]"
	@echo "make ui         start the web UI (Streamlit)"
	@echo "make build      build a fresh wheel and sdist into dist/"

poetry:
	@if command -v $(POETRY) >/dev/null 2>&1; then $(POETRY) --version; \
	else curl -sSL https://install.python-poetry.org | python3 - && \
	echo "Poetry installed. If 'poetry' is not found, add ~/.local/bin to your PATH."; fi

install: poetry
	$(POETRY) install --all-extras

test:
	$(POETRY) run pytest -q $(ARGS)

inspect:
	@test -n "$(FILE)" || { echo "Usage: make inspect FILE=path/to/data.csv [OUT=.] [FORMAT=markdown|json|both]"; exit 2; }
	$(POETRY) run sdi inspect "$(FILE)" -o "$(OUT)" $(if $(FORMAT),--format $(FORMAT))

ui:
	$(POETRY) run streamlit run smart_data_inspector/ui/app.py

build:
	rm -rf dist
	$(POETRY) build
