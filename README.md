# Smart Data Inspector

A local tool for a first look at an unfamiliar dataset. Give it one CSV, JSON, JSON Lines or Parquet file and it writes a readable Markdown report and/or a JSON report. The report covers the file's structure, missing values, duplicates, numeric/categorical/date summaries, and data-quality findings that come with explainable rules. It never changes the input file.

## Setup

```sh
make poetry     # installs Poetry if it is missing
make install    # poetry install --all-extras (CLI, tests and the web UI)
```

Without Make: `poetry install --all-extras` (or `pip install -e ".[dev,ui]"`).

## Run

```sh
make inspect FILE=path/to/data.csv                         # report in the current directory
make inspect FILE=data.json OUT=reports/ FORMAT=both       # Markdown + JSON in reports/
poetry run sdi inspect data.parquet -o report.md           # an exact report path
make ui                                                    # web UI at http://localhost:8501
```

- **Input:** a file path is required.
- **Output (`-o/--output`):**
  - Defaults to the current directory, writing `<input>_<run-id>.md` and `<input>_<run-id>_assets/` (charts). A new run never overwrites an earlier one.
  - A path ending in `.md` or `.json` writes exactly that file, with charts in `<name>_assets/`.
- **Format (`-f/--format`):** `markdown` (default), `json` or `both`.
- **Other options:** `--no-charts`, `--flatten-json`, `--missing-threshold`, `--iqr-multiplier`, `--top-values`, `--missing-value TOKEN` (repeatable) and `--no-missing-markers`.
- **Failure safety:** reports and charts are written to a hidden staging folder and moved into place together. A failed run leaves nothing half-written, and an earlier report at the same path is kept. A chart that fails or doesn't apply is listed with its reason in the report's *Chart availability* table.

The web UI (`smart_data_inspector/ui/app.py`) calls the same `run_inspection` workflow as the CLI. It always writes both report formats, then shows the files it wrote: summary metrics, the rendered report with its charts, findings, a column table, the chart gallery, and download buttons.

## Supported inputs

| Format | What is accepted |
| --- | --- |
| CSV | UTF-8 (optional BOM), comma-separated, unique non-blank header. Read in blocks with pyarrow; every value stays text until type inference. Short or long rows, unclosed quotes, duplicate headers and invalid UTF-8 are rejected with a message. |
| JSON | A top-level array of flat objects, streamed with `ijson`. Missing keys are treated as missing values. Files over 1 GiB are refused with a hint to convert them. |
| JSON Lines (`.jsonl`, `.ndjson`) | One flat object per line, read line by line. This is the cheap path for large data. |
| Parquet | Flat columns, loaded as Arrow-backed pandas columns. Nested and binary columns are rejected. |

With `--flatten-json`, nested objects become dotted columns (`lattice.a`), lists become compact JSON text, and a top-level object mapping keys to records gets a `_key` column. This lets the supplied `materials_piezoelectric_structures.json` (3,317 rows × 18 columns) be inspected. Without the flag, nested JSON is rejected with a hint.

## What the report checks

- **Structure:** row and column counts, inferred type per column (integer, number, boolean, datetime, string, mixed, empty), identifier-like columns.
- **Missing values:** per column, per record, the most common sets of fields missing together, and pairs of fields missing in the same records.
  - Text markers (`NA`, `N/A`, `n/a`, `#N/A`, `NULL`, `null`, `NaN`, `nan`) count as missing only on an exact, case-sensitive match. `Na` (sodium) and `none` are kept.
  - Every conversion is counted per column.
  - A warning appears when a marker such as `NA` sits among short codes like `K`, `Cl` or `Fe`.
- **Numbers:** min, max, mean, median, mode, standard deviation, variance, quartiles, skewness, kurtosis, zero share; IQR outlier candidates; constant or near-constant columns; columns that are mostly zero; strong correlations.
- **Text and categories:** top values, rare categories, whitespace and case variants, string length summaries.
- **Dates and times:** earliest and latest value, span, values after the inspection time, invalid calendar dates (e.g. `2024-02-30`), mixed layouts (ISO variants, non-ISO text like `05/01/2024`, timezone-aware mixed with naive).
- **Duplicates:** exact duplicate rows and duplicate columns.

Every finding records what was detected (evidence), the rule applied and why it matters. Findings are prompts for investigation, not automatic corrections.

## Demonstration reports

| Report | Input |
| --- | --- |
| `reports/materials_piezoelectric_properties.md/.json` | Supplied CSV, unchanged |
| `reports/structures_with_issues.md/.json` | Flat JSON with deliberately introduced problems (`data/demo/structures_with_issues.json`, made by `scripts/prepare_demo_data.py`) |
| `reports/materials_piezoelectric_properties_parquet.md/.json` | The CSV converted with `scripts/convert_csv_to_parquet.py` (`data/demo/…parquet`) |

## Checks and tests

```sh
make test          # 444 tests; every test runs in its own temporary directory
make build         # fresh wheel and sdist in dist/
```

- **Main workflow:** `make inspect FILE=data/demo/structures_with_issues.json` reports the duplicate row, the 23.8% missing `lattice_volume`, the `not measured` text in a numeric column and the extreme `lattice_a`.
- **Edge case:** a CSV with a short row, e.g. `printf 'a,b\n1,2\n3\n' > bad.csv && poetry run sdi inspect bad.csv`, exits with code 2, prints `Invalid CSV: … Expected 2 columns, got 1`, and writes no report.

## Limits

- The whole table is held in memory once loaded. Use Parquet or JSON Lines for big files.
- Type, identifier and date inference are heuristics. Only ISO-like date text is parsed; other date-looking text is reported, not guessed.
- The streaming JSON parser replaces invalid lone-surrogate escapes (`\ud800`) with `?`. JSON Lines input rejects them.
- No checks on units, domain rules or causality.
