# Data Inspection Report

## Overview

| Metric | Value |
| --- | --- |
| Source | examples/structures_with_issues.json |
| Format | JSON |
| Rows | 21 |
| Columns | 8 |
| Duplicate rows (beyond first) | 1 |
| Potential quality findings | 3 |

## Data quality findings

These are review prompts, not proof of invalid data.

| Rule | Column | Explanation / suggested action |
| --- | --- | --- |
| Duplicate rows | (whole dataset) | 1 repeated row(s) beyond the first occurrence after missing-value normalization. Check whether these are intended replicates. |
| High missingness | volume | 5/21 values are missing (23.8%), meeting the 20.0% threshold. Check collection coverage before relying on this column. |
| Mixed value types | volume | Observed number: 15, string: 1. Check unexpected tokens or inconsistent encoding; mixed categorical codes can also be legitimate. |

## Columns

| Column | Inferred type | Missing | Missing % | Distinct (non-missing) | Observed types |
| --- | --- | --- | --- | --- | --- |
| material_id | string | 0 | 0.0% | 20 | string: 21 |
| charge | number | 0 | 0.0% | 1 | number: 21 |
| lattice_a | number | 0 | 0.0% | 20 | number: 21 |
| lattice_b | number | 0 | 0.0% | 20 | number: 21 |
| lattice_c | number | 0 | 0.0% | 20 | number: 21 |
| site_count | integer | 0 | 0.0% | 15 | integer: 21 |
| elements | string | 0 | 0.0% | 20 | string: 21 |
| volume | mixed | 5 | 23.8% | 15 | number: 15, string: 1 |

## Numeric summaries

Only numeric cells are included; missing values, text and booleans are excluded. For mixed columns, statistics describe the numeric subset only. Values are shown to six significant digits.

| Column | Numeric values | Minimum | Maximum | Mean |
| --- | --- | --- | --- | --- |
| charge | 21 | 0.0 | 0.0 | 0 |
| lattice_a | 21 | 3.87458 | 14.1533 | 6.60264 |
| lattice_b | 21 | 4.26464 | 14.1533 | 7.05747 |
| lattice_c | 21 | 4.27419 | 16.6939 | 8.33355 |
| site_count | 21 | 3 | 56 | 19.3333 |
| volume | 15 | 128.133 | 669.012 | 323.620 |

## Categorical summaries

String, boolean and mixed columns; up to 3 most frequent non-missing values. Counts use original values, with ties in first-seen order. Strings are quoted to distinguish them from numbers.

| Column | Unique values | Most frequent values (count) |
| --- | --- | --- |
| material_id | 20 | "mp-aaaabwma" (2); "mp-aaaabuic" (1); "mp-aaaabuio" (1) |
| elements | 20 | "Li, P" (2); "C, F, O" (1); "Nd, O, Te" (1) |
| volume | 15 | 470.8186608267129 (2); "not measured" (1); 298.11228727832986 (1) |

## Rules and limitations

- Missingness: JSON null, absent keys and blank/whitespace-only strings are always missing. Configured text markers (case-insensitive, trimmed): "", "n/a", "na", "nan", "none", "null".
- High missingness: missing fraction >= 20.0%, including fully missing columns.
- Duplicates: repeated full rows beyond their first occurrence, after missing-value normalization. Original CSV strings are otherwise unchanged; JSON 1 and 1.0 compare equal, but true and 1 do not.
- Types: CSV recognizes signed integers, decimal/scientific numbers and true/false (case-insensitive). JSON preserves native types, so quoted numbers remain strings. Integer and number are compatible; other combinations trigger the mixed-type rule. Entirely missing columns are typed empty.
- Mixed types can be intentional in identifiers or categorical codes (for example, point groups). No domain schema or expected units are assumed; dates remain strings.
- Summary statistics include duplicate rows. Missing values are excluded from distinct counts and frequency tables. No rows are repaired, removed or imputed, and the source file is never modified.
- Scope: UTF-8 comma-separated CSV with a header, or a JSON array of flat objects. The full dataset is loaded into memory. No nested JSON, JSON Lines, outlier detection or domain validation.
