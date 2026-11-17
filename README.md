# Smart Data Inspector

Smart Data Inspector is a local-first, researcher-centric first-pass investigation tool for unfamiliar CSV and flat JSON datasets. Give it one path; it produces a readable Markdown note with evidence, recommendations, and appropriate PNG charts. It helps a researcher understand what the file contains, what deserves scrutiny, and what to investigate next. It does not clean data or claim scientific validity.

## Quick start

```sh
python -m pip install -e ".[dev]"
sdi --help
sdi inspect path/to/dataset.csv
sdi inspect path/to/dataset.json
```

`smart-data-inspector` remains available as a compatibility command. The usual workflow needs no options. Advanced options include `--missing-threshold`, `--iqr-multiplier`, `--top-values`, repeated `--missing-value`, `--no-charts`, and `--output REPORT.md`.

By default every run receives a UTC timestamp/nonce identifier. Reports go to `reports/<dataset>_<run-id>.md`; charts go to the matching `assets/<dataset>_<run-id>/` directory. Old runs are never overwritten. Image references are relative, so a report and the project directory can be moved together. `--output` chooses an explicit report destination for automation.

## Inputs

- UTF-8 comma-separated CSV with a nonblank, unique header.
- JSON only when it is a top-level array of flat objects. Missing object keys are missing values.

Nested JSON, arrays inside objects, JSON Lines, malformed CSV, empty files, duplicate headers, and unsupported extensions are rejected with an explanation. The source is never changed.

## What the report covers

The first page has dataset size and type mix, completeness, exact duplicate summary, an initial assessment, and the most important findings. The narrative then covers schema, missingness, selected numerical distributions, categorical consistency, correlations, prioritised quality concerns, and suggested next investigations. A technical appendix retains complete schema, numerical summaries, and rule evidence.

Profiling includes semantic type hints (integer, float, boolean, string, datetime, mixed, empty), identifiers, cardinality, missingness co-occurrence, row burden, duplicates, text length/formatting signals, numerical quantiles/variance/skewness/kurtosis/zeros, IQR candidates, Pearson and Spearman associations, constant/near-constant fields, rare categories, duplicate columns, and configurable quality thresholds. Statistical signals are deliberately described as observations rather than automatic errors.

Charts are generated only where appropriate: ranked missingness, row missingness, selected numerical histograms and boxplots, one low-cardinality frequency plot, and a numerical correlation heatmap. Matplotlib uses the non-interactive `Agg` backend and each chart failure is isolated from the rest of an inspection.

## Development

```sh
make help
make dev
make test
make test-file FILE=tests/unit/profiling/test_missingness.py
make test-dir DIR=tests/unit/quality
make inspect FILE=data/demo/structures_with_issues.json
```

GNU Make is normally present on macOS/Linux; Windows users may install it separately or run the shown Python commands directly. See [the extension guide](docs/EXTENDING_SMART_DATA_INSPECTOR.md) for the one-module/one-test convention and registration process.

## Demonstration datasets

The assessment examples are outside this package at `../JobMatchAssessment/OptionB_ExampleDatasets`. The project ships a supported flat JSON example at `data/demo/structures_with_issues.json`; its source preparation script is `scripts/prepare_demo_data.py`. The original supplied nested structures file is intentionally unsupported by the generic flat-JSON loader.

## Limits

The complete table is loaded in memory. Heuristics cannot establish units, field semantics, collection quality, domain constraints, causality, or fitness for a particular model. Float64 calculations have normal precision and range limits. Date inference is intentionally restricted to ISO-like strings to avoid guessing ambiguous values.

## Reference research

`docs/FG_DATA_PROFILING_RESEARCH.md` records the feature and algorithm study that informed this independent implementation. Smart Data Inspector does **not** install, import, wrap, or use `fg-data-profiling` or `ydata-profiling`.
