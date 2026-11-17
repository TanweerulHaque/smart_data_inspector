# Smart Data Inspector

Point it at a CSV, JSON, JSON Lines or Parquet file and it writes a data-quality report in Markdown, JSON or both. The report describes the file's structure, missing values, duplicates and column summaries, and lists possible problems with the rule that found each one. The input file is never modified.

## Setup

```sh
make poetry     # install Poetry if it is missing
make install    # install the CLI, tests and web UI
```

Without Make, run `poetry install --all-extras` or `pip install -e ".[dev,ui]"`.

## Usage

```sh
make inspect FILE=data.csv                            # report in the current directory
make inspect FILE=data.json OUT=reports/ FORMAT=both  # Markdown and JSON in reports/
poetry run sdi inspect data.parquet -o report.md      # exact report path
make ui                                               # web UI at http://localhost:8501
```

| Option | Effect |
| --- | --- |
| `FILE` / input path | Required. |
| `-o`, `--output` | A directory (default: current) or a path ending in `.md` or `.json`. A directory gets `<input>_<run-id>.md` plus `<input>_<run-id>_assets/`, so runs never overwrite each other. |
| `-f`, `--format` | `markdown` (default), `json` or `both`. |
| `--no-charts` | Skip PNG charts. |
| `--flatten-json` | Read nested JSON (see below). |
| `--missing-value TOKEN` | Replace the default missing-value markers. Repeatable. |
| `--no-missing-markers` | Treat only blanks and nulls as missing. |
| `--missing-threshold`, `--iqr-multiplier`, `--top-values` | Tune the rules. |

Reports and charts are written to a hidden staging folder and then moved into place together. If a run fails, it leaves no partial output and keeps any earlier report at that path. Charts that fail or don't apply are listed, with the reason, in the report's *Chart availability* table.

The web UI runs the same code as the CLI and always writes both formats. It then shows what the run wrote: summary metrics, the report with its charts, findings, column details, a chart gallery and download buttons.

## Supported inputs

| Format | Rules |
| --- | --- |
| CSV | UTF-8 (BOM allowed), comma-separated, unique non-blank header. Rows with too few or too many fields, unclosed quotes, duplicate headers and invalid UTF-8 are rejected with an error message. |
| JSON | A top-level array of flat objects, streamed with ijson. A missing key counts as a missing value. Files over 1 GiB are rejected; convert them to JSON Lines, CSV or Parquet. |
| JSON Lines (`.jsonl`, `.ndjson`) | One flat object per line. Use this for large files. |
| Parquet | Flat columns only; nested and binary columns are rejected. |

Nested JSON is rejected unless you pass `--flatten-json`. With the flag, nested objects become dotted columns (`lattice.a`) and lists become JSON text. A top-level object of records also works: each key goes into a `_key` column. This is how the supplied `materials_piezoelectric_structures.json` loads, as 3,317 rows × 18 columns.

## What the report covers

- **Structure:** rows, columns, an inferred type for each column, and columns that look like identifiers.
- **Missing values:** counts per column and per row, plus which fields tend to be missing together. A text marker such as `NA`, `N/A`, `NULL` or `NaN` counts as missing only on an exact, case-sensitive match, so `Na` (sodium) and `none` are kept as values. Each conversion is counted. If `NA` appears among short codes like `K` or `Cl`, the report warns that it may be a real value.
- **Numbers:** min, max, mean, median, mode, spread, quartiles, skewness, kurtosis and share of zeros. Rules flag IQR outliers, constant columns, mostly-zero columns and strong correlations.
- **Text and categories:** top values, rare categories, whitespace and case variants, and string lengths.
- **Dates:** earliest and latest values, dates later than the run time, impossible dates such as `2024-02-30`, and mixed formats (for example `2024-01-05` alongside `05/01/2024`).
- **Duplicates:** repeated rows and identical columns.

Each finding states what was found, the rule that flagged it and why it may matter. The tool reports problems but does not change any data.

## Example reports

| Report in `reports/` | Input |
| --- | --- |
| `materials_piezoelectric_properties` | The supplied CSV, unchanged |
| `structures_with_issues` | A flat JSON built from the supplied structures file with deliberate problems added (`scripts/prepare_demo_data.py`) |
| `materials_piezoelectric_properties_parquet` | The CSV converted to Parquet (`scripts/convert_csv_to_parquet.py`) |

Each report has a `.md` file, a `.json` file and an `_assets/` folder of charts.

## Tests

```sh
make test     # 444 tests, each in its own temporary directory
make build    # wheel and sdist in dist/
```

- **Main workflow:** `make inspect FILE=data/demo/structures_with_issues.json` reports the duplicate row, `lattice_volume` 23.8% missing, the text `not measured` in a numeric column, and the extreme `lattice_a` value.
- **Edge case:** `printf 'a,b\n1,2\n3\n' > bad.csv && poetry run sdi inspect bad.csv` exits with code 2, prints `Invalid CSV: … Expected 2 columns, got 1`, and writes no report.

## Limits

- The loaded table is held in memory. Prefer Parquet or JSON Lines for large data.
- Type, identifier and date detection are heuristics. Only ISO-style dates are parsed; other date-like text is reported, not guessed.
- In `.json` arrays, an invalid escape such as `\ud800` becomes `?`. JSON Lines rejects it.
- The tool does not check units, domain rules or causality.
