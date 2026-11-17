# Smart Data Inspector

A small, local **CLI-only** inspection tool for one CSV or JSON file at a time. It writes a Markdown report; no frontend, server, network calls, or runtime dependencies.

## Setup

Requires **Python 3.11+**. From this project directory, activate your existing environment in Zsh:

```sh
emulate bash -c '. /Users/tanweerulhaque/Library/Caches/pypoetry/virtualenvs/smart-data-inspector-vIYY8klk-py3.11/bin/activate'
python --version
```

On another machine, a standard environment is sufficient:

```sh
python3 -m venv .venv
. .venv/bin/activate
```

No installation is needed for `python -m smart_data_inspector` when run from this directory. Optionally, `poetry install` installs the equivalent `smart-data-inspector` command. Poetry may need network access to obtain its build dependencies; the inspector itself works offline.

## Run

```sh
python -m smart_data_inspector path/to/data.csv
python -m smart_data_inspector path/to/data.json -o reports/data.md
python -m smart_data_inspector --help
```

- Accepts exactly **one input file** per invocation. Inspect CSV and JSON separately.
- Default output: beside the input, named `<input-stem>.report.md`.
- `-o` / `--output`: choose a `.md` file; missing parent directories are created.
- An existing output report is replaced. The input cannot be overwritten, including through symbolic or hard links.
- Success prints only the report path to stdout and exits **0**, even when quality issues are found. Invalid input, options, or output produce an understandable stderr error and exit **2**.

### Configuration

```sh
python -m smart_data_inspector data.csv -o reports/custom.md \
  --missing-threshold 0.4 --top-values 5 \
  --missing-value NA --missing-value UNKNOWN
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--missing-threshold` | `0.2` | Flag missingness **at or above** this fraction; must be in `(0, 1]`. `0.4` means 40%. |
| `--top-values` | `3` | Maximum frequent values shown per categorical column; positive integer. |
| `--missing-value` | `NA`, `N/A`, `null`, `none`, `nan`, empty string | Repeat to **replace**, not extend, the default text markers. Matching ignores surrounding whitespace and case. |

JSON null, omitted keys, and empty/whitespace-only strings are always missing. To keep literal `NA` as a category while treating only blanks/nulls as missing, pass `--missing-value ''`.

## Report contents and rules

- Row/column counts, column names, inferred types, and observed type counts.
- Missing count and percentage, plus distinct non-missing count, for every column.
- Duplicate full-row count: repeated occurrences **beyond the first**, after missing-value normalization.
- Numeric count, minimum, maximum, and arithmetic mean. Missing/text/boolean cells are excluded. Numeric summaries of mixed columns describe **only their numeric subset**. Duplicates remain in statistics; displayed numbers use six significant digits.
- Categorical unique count and most frequent values with counts. Missing values are excluded; ties use first appearance. Frequencies retain original values, so CSV `001` and `1` remain different categories.
- Three explainable review rules: **high missingness**, **duplicate rows**, and **mixed value types**. Findings include evidence and a suggested check. No silent repairs, deduplication, or imputation.

CSV inference recognizes signed integers, decimal/scientific numbers, and case-insensitive `true`/`false`. Numeric zero/one are not booleans. JSON retains native types: `"12"` is a string, not a number. Integers and decimal numbers are compatible. All other combinations are `mixed`; entirely missing columns are `empty`. JSON `1` and `1.0` compare equal for frequencies and duplicates, but `true` and `1` do not. Decimal arithmetic avoids binary floating-point artifacts in summaries.

### Supported inputs and limitations

- CSV: UTF-8, comma-separated, with a non-empty, unique header. Optional UTF-8 BOM, quoted commas/newlines, and blank physical lines are supported. Records with the wrong field count are rejected, not skipped. Header names are preserved; a header cannot be detected reliably if a headerless file's first row looks like names.
- JSON: a top-level **array of flat objects**. Keys are combined in first-seen order; absent keys become missing values. Duplicate object keys, nested objects/arrays, object-root mappings, JSON Lines, and non-standard `NaN`/`Infinity` constants are rejected with explanations.
- Empty files, header-only CSV, `[]`, and tables without columns are rejected. Rows with all values missing are valid and still reported.
- The complete dataset is loaded into memory. Intended for small/medium local datasets, not streaming or distributed processing. Extremely large numeric magnitudes may exceed the available arithmetic/resources.
- No schema, units, datetime parsing, outlier detection, or domain-specific validation. Numeric-looking IDs can be inferred as numeric. Mixed codes can be legitimate; a warning does not establish an error. No findings does not guarantee clean data.

## Included demonstrations

The provided CSV can be inspected directly. **The provided JSON is actually a nested object mapping, outside the assessment's required flat-array format.** Rather than silently guessing how to flatten arbitrary JSON, a separate, dataset-specific CLI extracts a small flat demo. The resulting JSON is included, with provenance and intentional issues documented in [examples/README.md](examples/README.md). The inspector itself is not tied to these datasets.

Run from this directory:

```sh
# Provided CSV, unchanged.
python -m smart_data_inspector \
  ../JobMatchAssessment/OptionB_ExampleDatasets/materials_piezoelectric_properties.csv \
  -o reports/materials_piezoelectric_properties.md

# Rebuild the bundled JSON demo from the provided nested source (optional).
python examples/prepare_demo.py \
  ../JobMatchAssessment/OptionB_ExampleDatasets/materials_piezoelectric_structures.json

# Inspect the bundled, flat JSON demo.
python -m smart_data_inspector examples/structures_with_issues.json \
  -o reports/structures_with_issues.md
```

Included reports:

| Input | Rows | Columns | Expected observations | Report |
| --- | ---: | ---: | --- | --- |
| Provided CSV | 3,322 | 15 | 0 duplicates; some low missingness; mixed numeric/text `point_group` codes | [CSV report](reports/materials_piezoelectric_properties.md) |
| Derived JSON | 21 | 8 | 1 duplicate; 5 missing `volume` values (23.8%); 1 `"not measured"` volume | [JSON report](reports/structures_with_issues.md) |

The `point_group` warning is likely a legitimate coding convention, not corruption. Its numeric-subset mean should **not** be interpreted as a physical metric. This illustrates why the rules are review prompts rather than automatic data-cleaning decisions.

The original assessment files stay outside this project and are not changed. Only the derived/modified JSON is bundled; the provided CSV is not duplicated. The included JSON and tests work without the assessment folder; regenerating it and rerunning the provided CSV need the original files at the paths above. No external datasets or services were used.

## Checks

```sh
python -m unittest discover -s tests -v
```

The standard-library tests cover CSV/JSON loading, exact numeric and categorical summaries, missing-key handling, duplicate semantics, configurable rules, Markdown escaping, actual CLI invocations, invalid formats/options, and source-overwrite protection. Numeric tests include large finite values and cancellation.

One quick edge-case check is to inspect the original nested JSON directly:

```sh
python -m smart_data_inspector \
  ../JobMatchAssessment/OptionB_ExampleDatasets/materials_piezoelectric_structures.json
```

Expected: exit **2**, an explanation that JSON must be an array of flat objects, and no report created. Automated tests also cover empty data and malformed records without needing these assessment files.

## Design

```text
smart_data_inspector/
  cli.py          argument parsing and output
  loaders.py      strict CSV/JSON loading
  inspector.py    configuration, summaries and quality checks
  report.py       Markdown rendering
examples/         reproducible flat JSON demo and its preparation CLI
reports/          generated assessment reports
tests/            standard-library unit and CLI tests
```

These are plain functions and small dataclasses: no framework, plugin system, database, frontend, or extra configuration files. Run options are explicit CLI flags.

## Suggested 2–3 minute terminal demo

1. Show `--help` and run the provided CSV command.
2. Use `cat reports/materials_piezoelectric_properties.md`; explain dimensions, summaries, and the `point_group` caveat.
3. Run the JSON command and `cat reports/structures_with_issues.md`; point out all three quality rules.
4. Show the unsupported nested-JSON message or run the test suite.

## AI assistance and submission notes

Implementation and tests were created with the **Zed coding agent (GPT-6.1 Sol), including delegated coding agents**. Verification included executing unit/CLI tests, generating both reports, and cross-checking example results against separately calculated source statistics. This is AI-assisted work; review the code and understand its assumptions before submission.

A short reflection draft is in [REFLECTION.md](REFLECTION.md). Record your actual time spent and personal review there before submitting. A demo recording is not generated by this project.
