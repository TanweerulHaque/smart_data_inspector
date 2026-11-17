# Data Inspection Report

## Overview

| Metric | Value |
| --- | --- |
| Source | ../JobMatchAssessment/OptionB_ExampleDatasets/materials_piezoelectric_properties.csv |
| Format | CSV |
| Rows | 3,322 |
| Columns | 15 |
| Duplicate rows (beyond first) | 0 |
| Potential quality findings | 1 |

## Data quality findings

These are review prompts, not proof of invalid data.

| Rule | Column | Explanation / suggested action |
| --- | --- | --- |
| Mixed value types | point_group | Observed integer: 1,313, string: 2,009. Check unexpected tokens or inconsistent encoding; mixed categorical codes can also be legitimate. |

## Columns

| Column | Inferred type | Missing | Missing % | Distinct (non-missing) | Observed types |
| --- | --- | --- | --- | --- | --- |
| material_id | string | 0 | 0.0% | 3,322 | string: 3,322 |
| formula_pretty | string | 0 | 0.0% | 2,817 | string: 3,322 |
| e_longitudinal_max | number | 0 | 0.0% | 3,231 | number: 3,322 |
| e_abs_max | number | 0 | 0.0% | 3,295 | number: 3,322 |
| band_gap | number | 6 | 0.2% | 3,205 | number: 3,316 |
| crystal_system | string | 0 | 0.0% | 7 | string: 3,322 |
| point_group | mixed | 0 | 0.0% | 21 | integer: 1,313, string: 2,009 |
| is_metal | boolean | 6 | 0.2% | 2 | boolean: 3,316 |
| formation_energy_per_atom | number | 6 | 0.2% | 3,315 | number: 3,316 |
| energy_above_hull | number | 6 | 0.2% | 2,050 | number: 3,316 |
| density | number | 0 | 0.0% | 3,322 | number: 3,322 |
| is_stable | boolean | 5 | 0.2% | 2 | boolean: 3,317 |
| theoretical | boolean | 5 | 0.2% | 2 | boolean: 3,317 |
| num_atoms_in_cell | integer | 0 | 0.0% | 69 | integer: 3,322 |
| num_distinct_elements | integer | 0 | 0.0% | 6 | integer: 3,322 |

## Numeric summaries

Only numeric cells are included; missing values, text and booleans are excluded. For mixed columns, statistics describe the numeric subset only. Values are shown to six significant digits.

| Column | Numeric values | Minimum | Maximum | Mean |
| --- | --- | --- | --- | --- |
| e_longitudinal_max | 3,322 | 0.0 | 91.5779 | 0.820654 |
| e_abs_max | 3,322 | 0.0 | 119.036 | 0.835579 |
| band_gap | 3,316 | 0.0 | 8.3751 | 2.47956 |
| point_group | 1,313 | -6 | 622 | 88.5225 |
| formation_energy_per_atom | 3,316 | -4.48897 | 4.68820 | -1.72703 |
| energy_above_hull | 3,316 | 0.0 | 4.88245 | 0.0454466 |
| density | 3,322 | 0.212291 | 13.1605 | 4.10656 |
| num_atoms_in_cell | 3,322 | 2 | 288 | 22.1969 |
| num_distinct_elements | 3,322 | 1 | 6 | 3.30042 |

## Categorical summaries

String, boolean and mixed columns; up to 3 most frequent non-missing values. Counts use original values, with ties in first-seen order. Strings are quoted to distinguish them from numbers.

| Column | Unique values | Most frequent values (count) |
| --- | --- | --- |
| material_id | 3,322 | "mp-aaaaaywi" (1); "mp-aaaabbsv" (1); "mp-aaaaakax" (1) |
| formula_pretty | 2,817 | "SiO2" (44); "ZnS" (13); "LiMnPO4" (10) |
| crystal_system | 7 | "Orthorhombic" (876); "Tetragonal" (586); "Monoclinic" (526) |
| point_group | 21 | "mm2" (641); "-42m" (289); "-43m" (284) |
| is_metal | 2 | "False" (3,238); "True" (78) |
| is_stable | 2 | "False" (2,050); "True" (1,267) |
| theoretical | 2 | "False" (1,766); "True" (1,551) |

## Rules and limitations

- Missingness: JSON null, absent keys and blank/whitespace-only strings are always missing. Configured text markers (case-insensitive, trimmed): "", "n/a", "na", "nan", "none", "null".
- High missingness: missing fraction >= 20.0%, including fully missing columns.
- Duplicates: repeated full rows beyond their first occurrence, after missing-value normalization. Original CSV strings are otherwise unchanged; JSON 1 and 1.0 compare equal, but true and 1 do not.
- Types: CSV recognizes signed integers, decimal/scientific numbers and true/false (case-insensitive). JSON preserves native types, so quoted numbers remain strings. Integer and number are compatible; other combinations trigger the mixed-type rule. Entirely missing columns are typed empty.
- Mixed types can be intentional in identifiers or categorical codes (for example, point groups). No domain schema or expected units are assumed; dates remain strings.
- Summary statistics include duplicate rows. Missing values are excluded from distinct counts and frequency tables. No rows are repaired, removed or imputed, and the source file is never modified.
- Scope: UTF-8 comma-separated CSV with a header, or a JSON array of flat objects. The full dataset is loaded into memory. No nested JSON, JSON Lines, outlier detection or domain validation.
