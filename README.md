# Smart Data Inspector

A reusable, local-first **Python CLI** for one unfamiliar CSV or flat JSON dataset at a time. It uses Pandas to profile data and writes a readable Markdown report with explainable quality findings. No frontend, database, network processing, LLM, or automatic data repair.

## Requirements and installation

- Python **3.11+** on macOS, Linux, or Windows.
- Runtime: **Pandas, NumPy, Rich**. Development: **pytest**. Dependency ranges are in `pyproject.toml`.
- Package installation may download libraries; inspection itself stays offline. Files and report contents are never sent to a service.

From this project directory, activate an existing Python environment, then run:

```sh
python -m pip install -e ".[dev]"
python -m smart_data_inspector --help
```

For runtime-only installation, use `python -m pip install .`.

If no environment exists, create one with `python -m venv .venv`, then activate it:

| Platform / shell | Activation |
| --- | --- |
| macOS / Linux, sh/bash/zsh | `. .venv/bin/activate` |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |

Use `python3` or `py -3.11` instead of `python` where required by your installation. All application commands below are shell-independent; paths containing spaces should be quoted.

For this assessment, development and verification reused the supplied Poetry-managed **Python 3.11.16** environment; no new environment was created. Verified library versions: Pandas 3.0.6, NumPy 2.4.6, Rich 14.3.4, pytest 9.2.0. macOS was exercised; Linux/Windows portability is designed for but was not tested on those operating systems.

## Run

```sh
python -m smart_data_inspector inspect path/to/dataset.csv --output reports/dataset.md
python -m smart_data_inspector inspect path/to/dataset.json --output reports/dataset.md
smart-data-inspector inspect path/to/dataset.csv --output reports/dataset.md
python -m smart_data_inspector inspect --help
```

- Exactly **one file per invocation**. The `inspect` subcommand is required.
- Default report: `<input-stem>.report.md` beside the source. Use `--output` to keep reports elsewhere.
- Missing report directories are created. Existing reports are replaced atomically, so a failed write does not truncate an existing report. Input-overwrite attempts, including symlinks and hard links, are rejected.
- Rich terminal output shows input, dimensions, missing cells, duplicates, findings, and report location. Dataset text is rendered literally, not as terminal markup.
- Exit **0**: report generated, including when quality issues are found. Exit **2**: invalid input, arguments, configuration, or output. Findings are review prompts, not process failures.

### Configuration

```sh
python -m smart_data_inspector inspect data.csv --output reports/custom.md --missing-threshold 0.10 --iqr-multiplier 3 --top-values 3
python -m smart_data_inspector inspect data.csv --missing-value NA --missing-value UNKNOWN
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--output`, `-o` | beside the input | Markdown destination; must end in `.md` |
| `--missing-threshold` | `0.05` | Inclusive high-missingness threshold as a fraction; `0.05` means **5%**, valid range `(0, 1]` |
| `--iqr-multiplier` | `1.5` | Positive, finite IQR fence multiplier |
| `--top-values` | `5` | Positive integer limiting frequent categorical values |
| `--missing-value` | blank, `NA`, `N/A`, `null`, `none`, `nan` | Repeat to **replace**, not extend, the default text markers; case-insensitive and trimmed |

JSON null, absent keys, and blank/whitespace-only strings are always missing. To retain literal `NA` categories, use `--missing-value ""`. Zero and false are never missing. Additional inference/identifier/sample-size defaults live centrally in `smart_data_inspector/config.py` and can be supplied through the Python API.

## Supported formats

**CSV:** UTF-8 (optional BOM), comma-separated, a nonblank unique header, rectangular records. Quoted commas/newlines and blank physical lines are supported. Wrong field counts, unterminated quoted records, invalid encoding, and duplicate/blank headers are rejected rather than silently skipped. A headerless file cannot always be distinguished from a valid header; a header is the caller's responsibility.

**JSON:** exactly a top-level array of flat objects:

```json
[
  {"sample_id": "A", "measurement": 1.2, "label": "control"},
  {"sample_id": "B", "measurement": null},
  {"sample_id": "C", "label": "treated"}
]
```

Keys are combined in first-seen order. Omitted keys and null become missing values. Native numbers, strings, and booleans retain their identity; `"12"` remains a string. Integer and decimal numbers are compatible. Duplicate keys, lone Unicode surrogates, nested objects/arrays, root mappings, JSON Lines, and nonstandard `NaN`/`Infinity` constants are rejected with explanations.

Empty files, header-only CSV, `[]`, and tables without columns return actionable errors. Single-row datasets and nonempty tables with all-null columns are valid. Individual pure profilers also handle zero rows without division by zero.

## Report contents

1. **Overview:** source name/path/extension, file size, row/column dimensions, approximate DataFrame memory.
2. **Overall summary:** missing cells/columns, additional duplicates, findings and severities.
3. **Schema inventory:** every column, inferred semantic type, non-null count, observed type evidence, identifier hints.
4. **Missing values:** counts and percentages for every column, including complete columns.
5. **Duplicates:** explicit counting definition and percentage.
6. **Numeric statistics:** finite count, excluded nonfinite count, min/max, mean, median, sample standard deviation (`ddof=1`), Q1/Q3 (linear interpolation).
7. **Categorical statistics:** distinct non-null values, most frequent value and frequency, top five by default. Likely identifiers suppress misleading modes/top values.
8. **Quality findings:** check name, column, severity, evidence, rule, explanation.
9. **Rules and interpretation limits.**

Unavailable values use `N/A`. Numbers use six significant digits, which is display formatting, not a claim about measurement precision. User-controlled text is escaped for Markdown. Memory is a deep DataFrame estimate, not peak process RAM.

### Explainable quality rules

| Check | Rule and interpretation |
| --- | --- |
| Missingness | Any missing values produce an informational finding; missing fraction **>= 5%** produces a warning by default. No imputation. |
| Duplicates | Warn when normalized full rows repeat. Count **additional occurrences beyond the first**, so three identical rows count as two. Only missing markers are normalized; CSV `001` and `1` remain distinct. Numeric JSON `1` and `1.0` compare equal; boolean `true` and numeric `1` do not. |
| Mixed/inconsistent types | Flag incompatible JSON native types. For CSV, numeric/text mixtures are flagged only when **>= 80%** of nonmissing values are numeric and the column is not a likely identifier. Below that, retain categorical strings rather than treating ordinary codes as errors. Booleans and numbers are incompatible. Examples of unexpected values are included. |
| Potential numerical outliers | Informational: values strictly below `Q1 - 1.5 × IQR` or above `Q3 + 1.5 × IQR`. Uses finite values; skips fewer than **4** values, zero IQR, and likely identifiers. These are potential outliers, **not confirmed errors**. |
| Nonfinite values | Warn about infinity or magnitudes beyond finite float64 range; exclude them from numeric statistics and IQR, and report excluded counts. NaN missing markers are handled as missing values instead. |

Identifier hints use an ID-like name with at least **95%** uniqueness, or an entirely unique semantic-text column with at least **10** non-null values. Numeric CSV measurements do not become identifiers merely because their raw tokens are unique strings. Hints are not key validation.

CSV inference recognizes integers, decimal/scientific numbers, and true/false. An entirely missing column is `empty`. Mixed-column numeric statistics describe **only the numeric subset**, explicitly labelled. Duplicates remain in statistics. No scientific ranges, units, or materials-specific assumptions are built into the engine. The example `point_group` codes remain categorical and receive no misleading numeric mean.

## Architecture and reusable API

The existing package location is retained rather than moved to `src/`; this preserves imports and avoids an unrelated packaging migration. Broad areas and individual feature folders have clear responsibilities:

```text
smart_data_inspector/
  config.py, models.py          central options and shared result dataclasses
  loaders.py, inspector.py      public loading API and profiling orchestration
  cli/main.py                   argparse, Rich presentation, exit codes
  ingestion/
    csv/loader.py               strict CSV parsing
    json/loader.py              flat-array JSON validation
  profiling/
    schema/, missingness/, numeric/, categorical/, duplicates/
  quality/
    missingness/, duplicates/, mixed_types/, outliers/
  reporting/markdown/renderer.py
  report.py                     compatibility import for render_report
  utils/                        scalar/JSON conversion, numeric safeguards, atomic output
scripts/prepare_demo_data.py     dataset-specific preprocessing, outside the engine
examples/                       preserved historical sample and converter wrapper
data/demo/                      current clean and deliberately flawed flat JSON
reports/                        the two generated assessment reports
tests/
  unit/                         independent profiler/check/renderer/parser/util tests
  integration/                  actual CLI subprocess tests
  test_*.py                     preserved and updated original regression tests
```

Strict standard-library parsing precedes a Pandas DataFrame so malformed CSV is rejected without dropping rows, and raw tokens remain available for type evidence and exact duplicate comparison. Pandas implements missingness, grouping, numeric summaries and quartiles. Small numeric safeguards handle overflow/cancellation without globally scaling away tiny quartiles. Plain functions and a few shared dataclasses avoid frameworks, plugins, inheritance, and hidden global state.

```python
from smart_data_inspector.config import InspectionConfig
from smart_data_inspector.inspector import inspect_dataset
from smart_data_inspector.loaders import load_dataset
from smart_data_inspector.report import render_report

result = inspect_dataset(load_dataset("data.csv"), InspectionConfig(missing_threshold=0.10))
markdown = render_report(result)
```

The report renderer is pure. Profilers/checks can be called independently on Pandas Series/DataFrames. `utils.serialization.dumps_json` provides strict JSON-safe conversion for reuse (not a second CLI output format): missing/nonfinite values become null, NumPy scalars become native values, and Decimals that cannot round-trip through a float are preserved as strings.

## Assessment demonstrations

The supplied structures JSON is a **nested object mapping**, not the assessment's required flat-array input. The generic loader deliberately rejects it. The separate preprocessing script reads the original without changing it and selects the first **20** structures in insertion order by default.

From this project directory:

```sh
python scripts/prepare_demo_data.py ../JobMatchAssessment/OptionB_ExampleDatasets/materials_piezoelectric_structures.json
python -m smart_data_inspector inspect ../JobMatchAssessment/OptionB_ExampleDatasets/materials_piezoelectric_properties.csv --output reports/materials_piezoelectric_properties.md
python -m smart_data_inspector inspect data/demo/structures_with_issues.json --output reports/structures_with_issues.md
```

The script writes both [clean flat JSON](data/demo/structures_flat.json) (**20 × 11**) and [issues JSON](data/demo/structures_with_issues.json) (**21 × 11**). Each flat record contains `material_id`, lattice `a/b/c/alpha/beta/gamma/volume`, `num_sites`, `num_distinct_elements`, and readable `elements`. The clean artifact means “no deliberate modifications,” not “scientifically validated.”

### Exact deliberate modifications

One-based row numbers in the issues JSON:

- Remove `lattice_volume` from rows **1, 3, 5**.
- Set `lattice_volume` to JSON null in rows **2, 4**.
- Replace row **6**'s `lattice_volume` with **`"not measured"`**.
- Multiply row **20**'s `lattice_a` by **100**, from `6.126698` to **`612.6698`**.
- Append row **21** as an exact copy of row 20, including the extreme value and material ID.

The original supplied files and historical `examples/structures_with_issues.json` are untouched. Detailed provenance, custom generator options, and small-input behavior are in [examples/README.md](examples/README.md). Both derived datasets come solely from the assessment materials; no external dataset or service was used. The bundled modified data can be inspected without the original assessment folder. Regenerating it and rerunning the CSV demonstration require the originals.

| Demonstration | Verified observations | Generated report |
| --- | --- | --- |
| Supplied CSV, **3,322 × 15** | **34** missing cells across 6 columns, **0** duplicates, **14** informational findings: 6 missingness and 8 IQR-column findings; no high missingness or mixed-code false alarm | [CSV report](reports/materials_piezoelectric_properties.md) |
| Derived issues JSON, **21 × 11** | **5/21 (23.81%)** missing volumes, **1** extra duplicate, unexpected `"not measured"`, introduced extreme detected; **9** findings (3 warnings, 6 informational) | [JSON report](reports/structures_with_issues.md) |

Some unmodified features also produce potential IQR outliers. This is expected distribution-based screening, not evidence of corrupted science. The duplicate repeats the injected extreme, so it occurs twice in the final data.

### One unsupported-format check

```sh
python -m smart_data_inspector inspect ../JobMatchAssessment/OptionB_ExampleDatasets/materials_piezoelectric_structures.json --output reports/unsupported_nested.md
```

Expected and verified: **exit 2**, an explanation requiring a top-level array of flat objects, and **no report created**. Neither original dataset is modified.

## Tests and verification

```sh
python -m pytest -q
python -m pytest tests/unit/profiling tests/unit/quality -q
python -m pytest tests/integration -q
python -m pip check
```

The complete suite covers loaders and malformed input, missing keys/nulls, type inference, numeric/categorical summaries, missingness, exact duplicates, mixed types, IQR, identifier hints, report escaping, single rows, all-null/zero-row profiling, special-value JSON serialization, actual CLI errors/output safety, and deterministic demo generation. It uses small temporary fixtures; the original 50 MB JSON is not needed for tests. Pytest also runs the retained unittest regressions.

Verification performed in the supplied environment: **433 tests and 86 unittest subtests passed**, both actual dataset commands, review of both Markdown reports, the unsupported original-JSON case, editable installation, console entry point, local wheel build, and dependency consistency check. Review-discovered regressions for unique numeric CSV columns, extreme-magnitude arithmetic, terminal markup, and invalid Unicode are covered by tests. Source SHA-256 checks confirmed both original datasets were unchanged.

### Limitations

- Full in-memory processing, intended for small/medium local data; not streaming or distributed.
- Float64 statistics can round large integers/high-precision decimals and underflow tiny values; exact scalar identity is retained for duplicates. Values outside finite float64 range are explicitly excluded and flagged. Unrepresentable statistics are `N/A`.
- No date inference, expected schema, domain constraints, physical validity checks, or automatic cleaning.
- Conservative mixed-type and identifier inference is heuristic and may miss issues or flag intentional encodings. Review evidence in context.
- Zero-IQR/small-sample outlier screening is intentionally skipped. Skewed distributions can produce many candidates.
- **Plots are not implemented**; they are optional, and Markdown inspection has no plotting prerequisite.

## Demo and submission checklist

A suggested 2–3 minute terminal walkthrough: show help; run the CSV; explain schema/missingness and `point_group`; run the issues JSON; identify all four check families; show the unsupported-format error and pytest result.

AI assistance: **Zed coding agent (GPT-6.1 Sol), including delegated agents**, assisted implementation, tests, documentation and an independent edge-case review. Findings were verified with executable tests and real CLI runs; this is not a substitute for the author's personal code review.

[REFLECTION.md](REFLECTION.md) is below the assessment's 300-word limit. Fill in actual time spent and personal-review notes before submission. The author still needs to record/present the required demo and package the project or publish an accessible repository. Include this project, both reports, and the bundled derived data; the optional `dist/` directory may contain historical 0.1.0 artifacts, so use the current 0.2.0 wheel or build from the project rather than distributing an old wheel.
