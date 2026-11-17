# Structure inspection demo

The canonical generator is [`scripts/prepare_demo_data.py`](../scripts/prepare_demo_data.py).
It uses only the Python standard library to read the supplied
[`materials_piezoelectric_structures.json`](../../JobMatchAssessment/OptionB_ExampleDatasets/materials_piezoelectric_structures.json),
a JSON object mapping material IDs to pymatgen Structure dictionaries. No pymatgen,
downloads, external sources, or inspection-engine imports are needed. The original
source and the historical `examples/structures_with_issues.json` are left intact.

## Reproduce

From the `smart_data_inspector` root, run:

```sh
python scripts/prepare_demo_data.py ../JobMatchAssessment/OptionB_ExampleDatasets/materials_piezoelectric_structures.json
```

The defaults, relative to the working directory, are:

- `--limit 20`: select the first `min(limit, source size)` records in source JSON
  insertion order. The limit must be a positive integer.
- `--clean-output data/demo/structures_flat.json`: **20 clean rows, 11 columns**
  with the supplied source and default limit.
- `--output data/demo/structures_with_issues.json`: **21 rows, 11 columns**
  (the union of keys), including an appended duplicate.

Both destination directories are created as needed. Each run with the same source
and arguments produces identical UTF-8 JSON bytes with a trailing newline. Existing
demo destinations may be overwritten, but neither output may overwrite the source
or refer to the other output, including through symbolic links, linked parent
directories, or hard links. Parent/child output paths are also rejected. Destinations
must have a `.json` extension (case-insensitive).

Malformed JSON, empty/non-object sources, malformed selected records, invalid
limits/paths, nonfinite numbers, and file errors produce actionable argparse errors
without tracebacks. Both destinations and all selected records are validated, and
both datasets are serialized, before either output is written. Only the selected
records are flattened and feature-validated; invalid later records do not prevent
using a smaller limit. Writes are not transactional if an operating-system write
fails after validation.

`examples/prepare_demo.py` remains a small compatibility wrapper that forwards all
CLI arguments to the canonical script, **including the new default destinations**.
To use custom paths or select fewer records:

```sh
python scripts/prepare_demo_data.py ../JobMatchAssessment/OptionB_ExampleDatasets/materials_piezoelectric_structures.json --limit 8 --clean-output data/demo/custom_clean.json --output data/demo/custom_issues.json
```

## The eleven flat features

| Field | Source / derivation |
| --- | --- |
| `material_id` | Top-level mapping key |
| `lattice_a`, `lattice_b`, `lattice_c` | Lattice `a`, `b`, `c` |
| `lattice_alpha`, `lattice_beta`, `lattice_gamma` | Lattice `alpha`, `beta`, `gamma` |
| `lattice_volume` | Lattice `volume`, before intentional corruption |
| `num_sites` | Length of the `sites` list |
| `num_distinct_elements` | Number of unique elements across all site species |
| `elements` | Sorted unique element strings, stripped and joined with `", "` |

Charge, coordinates, matrices, and metadata are intentionally excluded. Selected
records must have a lattice object with all seven finite numeric features (not
booleans), a sites array, and nonempty species arrays containing nonblank element
strings. Empty sites arrays yield zero counts and an empty elements string. No
external chemistry validation is attempted.

## Exact intentional issues

Let `n` be the selected row count **before** duplication. The clean rows are copied
before defects are injected, leaving `structures_flat.json` unchanged:

1. In the first `ceil(n / 4)` rows, alternate **omitting** `lattice_volume`
   (rows 1, 3, 5, ...) and setting it to JSON **null** (rows 2, 4, ...).
2. If any rows remain, replace the next row's `lattice_volume` with the string
   **`"not measured"`**. With `n = 1`, there is no next row, so this step is skipped.
3. Multiply the last selected row's `lattice_a` by **100** to demonstrate an
   extreme numeric value and IQR-based outlier detection. Reject overflow rather
   than emitting Infinity. With tiny/custom inputs, IQR detection is not guaranteed.
4. Append an **exact copy of the last row**, including its material ID and all
   previously applied defects. This also repeats the extreme `lattice_a` value.
   For tiny inputs the duplicate can repeat a missing or nonnumeric volume.

For the supplied source and default `--limit 20`, row numbers are one-based:

| Introduced issue | Exact rows / values |
| --- | --- |
| 3 absent `lattice_volume` keys | Rows 1 (`mp-aaaabuic`), 3 (`mp-aaaabuma`), 5 (`mp-aaaabunu`) |
| 2 null `lattice_volume` values | Rows 2 (`mp-aaaabuio`), 4 (`mp-aaaabunr`) |
| 1 nonnumeric `lattice_volume` | Row 6 (`mp-aaaabunv`): `"not measured"` |
| 1 selected row with extreme `lattice_a` | Row 20 (`mp-aaaabwma`): `6.126698 * 100 = 612.6698` |
| 1 appended exact duplicate | Row 21 exactly equals row 20 (`mp-aaaabwma`), including `lattice_a = 612.6698` |

Thus missing volume affects **5/21 rows (23.81%)** in the final issues file, and the
introduced extreme occurs in **2 rows after duplication**. These are intentional
demonstration defects, not repairs or changes to the original structures. The clean
file retains original feature values and may still exhibit natural variation.

## Focused tests

The tests load the generator using `importlib` and do not import the inspection
engine. With pytest available in the existing environment:

```sh
python -m pytest tests/unit/test_demo.py -q
```

They cover the eleven features, validation, exact defects (including tiny inputs),
IQR extremity, determinism, default and explicit destinations, directory creation,
source/output alias protection, errors without tracebacks, and wrapper forwarding.
