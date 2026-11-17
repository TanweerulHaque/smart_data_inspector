# Structure inspection demo

`prepare_demo.py` uses only the Python standard library. It reads the provided
[`materials_piezoelectric_structures.json`](../../JobMatchAssessment/OptionB_ExampleDatasets/materials_piezoelectric_structures.json),
a JSON object mapping material IDs to pymatgen Structure dictionaries. No pymatgen
installation, downloads, or external sources are needed. The source is not modified.

## Reproduce

From the `smart_data_inspector` root, run:

```sh
/Users/tanweerulhaque/Library/Caches/pypoetry/virtualenvs/smart-data-inspector-vIYY8klk-py3.11/bin/python examples/prepare_demo.py ../JobMatchAssessment/OptionB_ExampleDatasets/materials_piezoelectric_structures.json
```

The defaults are `--limit 20` and
`--output examples/structures_with_issues.json` (relative to the working directory).
The limit must be a positive integer. The script selects the first `min(limit,
source size)` structures in JSON insertion order, then appends one duplicate.
The checked-in example therefore has **21 rows and 8 columns** (the union of keys).
Each run with the same source and arguments produces identical output bytes.
Malformed JSON, an empty/non-object source, malformed selected records, file errors,
and attempts to overwrite the source produce argparse errors without tracebacks.
The destination directory must already exist.

## Fields

| Field | Source / derivation |
| --- | --- |
| `material_id` | Top-level mapping key |
| `charge` | Structure `charge` |
| `lattice_a`, `lattice_b`, `lattice_c` | Lattice `a`, `b`, `c` |
| `volume` | Lattice `volume`, before intentional corruption |
| `site_count` | Length of the `sites` list |
| `elements` | Sorted, unique `element` values across all site `species`, joined with `", "` |

Only these fields are retained; angles, coordinates, metadata, and other nested
properties are excluded. Selected records must have numeric charge/lattice values
and a sites list with valid species element strings.

## Intentional issues

Let `n` be the number of selected structures **before** duplication. Issues are
injected in this fixed order (row numbers below are one-based):

1. In the first `ceil(n / 4)` rows, alternate **omitting** the `volume` key
   (rows 1, 3, 5, ...) and setting it to JSON **null** (rows 2, 4, ...).
   For small inputs where only one volume is removed, it is omitted.
2. If any rows remain, replace the next row's numeric `volume` with the string
   **`"not measured"`**. With `n = 1`, no remaining numeric volume is available.
3. Append an **exact copy of the last row**, including its material ID and any
   defects already applied to it. This guarantees at least one duplicate pair.

For the default 20 selected structures, the checked-in JSON contains exactly:

- **3 omitted volumes:** rows 1, 3, and 5.
- **2 null volumes:** rows 2 and 4.
- **1 nonnumeric volume:** row 6 (`mp-aaaabunv`), set to `"not measured"`.
- **1 appended duplicate:** row 21 exactly equals row 20 (`mp-aaaabwma`).

These defects are deliberate demonstration data, not repairs to the original
structures. The appended row does not add another volume defect in the default run.
