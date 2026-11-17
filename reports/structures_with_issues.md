# Data Inspection Report

## Overview

| Metric | Value |
| --- | --- |
| Source file | structures_with_issues.json |
| Source path | data/demo/structures_with_issues.json |
| Extension | .json |
| Format | JSON |
| File size | 7,434 bytes (7.25977 KiB) |
| Rows | 21 |
| Columns | 11 |
| Estimated in-memory size | 20,405 bytes (19.9268 KiB) |

Memory is the reported data-memory estimate, not peak process memory.

## Overall summary

- Missing cells: 5 across 1 column(s).
- Additional duplicate rows: 1.
- Potential quality findings: 9.
- Findings by severity: info: 6, warning: 3.

Findings are review prompts, not proof of invalid data or scientific validity.

## Schema inventory

Non-null counts are after missing-value normalization. Inferred semantic types describe how columns are interpreted; observed scalar types show the evidence used for inference.

| Column | Non-null | Inferred semantic type | Observed types (count) | Likely identifier |
| --- | --- | --- | --- | --- |
| material_id | 21 | string | string: 21 | Yes |
| lattice_a | 21 | number | number: 21 | No |
| lattice_b | 21 | number | number: 21 | No |
| lattice_c | 21 | number | number: 21 | No |
| lattice_alpha | 21 | number | number: 21 | No |
| lattice_beta | 21 | number | number: 21 | No |
| lattice_gamma | 21 | number | number: 21 | No |
| num_sites | 21 | integer | integer: 21 | No |
| num_distinct_elements | 21 | integer | integer: 21 | No |
| elements | 21 | string | string: 21 | No |
| lattice_volume | 16 | mixed | number: 15, string: 1 | No |

## Missing values

All columns are listed. High missingness means at least 5% missing.

| Column | Missing | Missing % | Non-null | High missingness |
| --- | --- | --- | --- | --- |
| material_id | 0 | 0% | 21 | No |
| lattice_a | 0 | 0% | 21 | No |
| lattice_b | 0 | 0% | 21 | No |
| lattice_c | 0 | 0% | 21 | No |
| lattice_alpha | 0 | 0% | 21 | No |
| lattice_beta | 0 | 0% | 21 | No |
| lattice_gamma | 0 | 0% | 21 | No |
| num_sites | 0 | 0% | 21 | No |
| num_distinct_elements | 0 | 0% | 21 | No |
| elements | 0 | 0% | 21 | No |
| lattice_volume | 5 | 23.8095% | 16 | Yes |

## Duplicate rows

The count is additional full-row occurrences beyond the first occurrence in each group, after missing-value normalization; it is not the number of all rows belonging to duplicate groups. For example, three identical rows contribute two additional rows.

| Metric | Value |
| --- | --- |
| Additional duplicate rows | 1 |
| Share of all rows | 4.7619% |

## Numeric summaries

Statistics use only the finite numeric subset, excluding missing values, text, booleans and nonfinite values. Mixed-column statistics describe the numeric subset only, not the full column. Counts include duplicate rows. Standard deviation is the sample standard deviation (ddof=1); it is undefined for fewer than two finite values. Quartiles use linear interpolation. Numbers are shown to six significant digits; N/A means undefined or unavailable.

| Column | Finite count | Nonfinite excluded | Minimum | Maximum | Mean | Median | Sample std (ddof=1) | Q1 (25%) | Q3 (75%) | Scope / notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lattice_a | 21 | 0 | 3.87458 | 612.67 | 64.3686 | 6.31483 | 182.306 | 4.77535 | 7.50944 | Finite numeric values |
| lattice_b | 21 | 0 | 4.26464 | 14.1533 | 7.05747 | 7.0268 | 2.46817 | 5.10925 | 8.07888 | Finite numeric values |
| lattice_c | 21 | 0 | 4.27419 | 16.6939 | 8.33355 | 8.10844 | 2.94537 | 6.93571 | 9.43009 | Finite numeric values |
| lattice_alpha | 21 | 0 | 17.2597 | 111.295 | 81.0827 | 90 | 24.3048 | 67.4524 | 90 | Finite numeric values |
| lattice_beta | 21 | 0 | 17.2597 | 111.295 | 83.8425 | 90 | 22.1282 | 90 | 90 | Finite numeric values |
| lattice_gamma | 21 | 0 | 17.2597 | 120 | 85.7445 | 90 | 23.2291 | 90 | 94.9272 | Finite numeric values |
| num_sites | 21 | 0 | 3 | 56 | 19.3333 | 20 | 13.4957 | 8 | 25 | Finite numeric values |
| num_distinct_elements | 21 | 0 | 2 | 4 | 2.66667 | 3 | 0.658281 | 2 | 3 | Finite numeric values |
| lattice_volume | 15 | 0 | 128.133 | 669.012 | 323.62 | 275.276 | 143.581 | 219.241 | 424.508 | Numeric subset only; not the full column |

## Categorical summaries

String, boolean and mixed columns, plus likely identifiers of any type. Up to 5 most frequent non-missing values are shown. Frequency uses the non-null count as denominator; ties retain first-seen order, so the displayed most frequent value need not be a unique mode. Strings are quoted to distinguish them from numbers. Likely identifiers, including numeric IDs, have their mode and top values suppressed to avoid misleading categorical interpretations.

| Column | Distinct (non-missing) | Most frequent value | Frequency (non-missing) | Top values (count) | Notes |
| --- | --- | --- | --- | --- | --- |
| material_id | 20 | N/A | N/A | N/A | Likely identifier; mode and top values suppressed |
| elements | 20 | "Li, P" | 2 / 21 (9.52381%) | "Li, P" (2); "C, F, O" (1); "Nd, O, Te" (1); "Al, B, O" (1); "Bi, Co, Zr" (1) |  |
| lattice_volume | 15 | 470.819 | 2 / 16 (12.5%) | 470.819 (2); "not measured" (1); 298.112 (1); 297.479 (1); 669.012 (1) |  |

## Data quality findings

Each finding preserves its check name, column, severity, evidence, rule and explanation.

| Check name | Column | Severity | Evidence | Rule | Explanation |
| --- | --- | --- | --- | --- | --- |
| Duplicate rows | (whole dataset) | warning | 1 repeated row(s) beyond the first occurrence. | Full-row equality after missing-value normalization; count additional occurrences only. | Check whether repeated records are intended replicates before removing anything. |
| Potential numerical outliers | lattice_a | info | 4/21 finite numeric values outside IQR fences \[0.674231, 11.6106\]. Examples: 13.4622, 14.1533, 612.67. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Potential numerical outliers | lattice_b | info | 1/21 finite numeric values outside IQR fences \[0.654785, 12.5333\]. Examples: 14.1533. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Potential numerical outliers | lattice_c | info | 2/21 finite numeric values outside IQR fences \[3.19415, 13.1717\]. Examples: 16.6939, 14.1533. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Potential numerical outliers | lattice_alpha | info | 2/21 finite numeric values outside IQR fences \[33.6311, 123.821\]. Examples: 30.3091, 17.2597. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Potential numerical outliers | lattice_gamma | info | 9/21 finite numeric values outside IQR fences \[82.6092, 102.318\]. Examples: 110.754, 60, 60, 60, 109.471. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Potential numerical outliers | num_sites | info | 1/21 finite numeric values outside IQR fences \[-17.5, 50.5\]. Examples: 56. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| High missingness | lattice_volume | warning | 5 missing of 21 values (23.81%). | High missingness when missing fraction &gt;= 5.0%; any missing values are reported. | Review collection coverage before relying on this column; no imputation has been performed. |
| Mixed value types | lattice_volume | warning | Observed number: 15, string: 1. Representative unexpected values: \['not measured'\]. | Incompatible JSON native types, or CSV numeric proportion &gt;= 80% with nonnumeric tokens; boolean/number mixtures are incompatible. | Review unexpected values or inconsistent encoding. Mixed codes can be intentional, not confirmed errors. |

## Rules and limitations

- Missingness: JSON null, absent keys and blank/whitespace-only strings are missing. Configured text markers (case-insensitive, trimmed): "", "n/a", "na", "nan", "none", "null". The high-missingness threshold is inclusive: missing fraction >= 5%.
- Duplicates compare full rows after missing normalization. Original CSV strings otherwise remain unchanged; numeric JSON 1 and 1.0 compare equal, but boolean true and numeric 1 do not. Repeated rows may be legitimate replicates.
- Types: CSV recognizes signed integers, decimal/scientific numbers and true/false (case-insensitive). Conservative mixed-numeric CSV inference requires at least 80% numeric non-missing values before treating numeric/text mixtures as mixed, and avoids flagging likely identifiers as damaged numeric data. Below that threshold such mixtures remain categorical strings. Integer and number are compatible. JSON preserves native types: quoted numbers and booleans remain strings. Entirely missing columns are empty.
- Identifier hints are heuristic, not keys or uniqueness guarantees: identifier-like names require at least 95% uniqueness among non-missing values; entirely unique text columns also qualify with at least 10 values. Mixed categorical codes can be intentional; no domain schema, expected units or dates are inferred.
- Numeric precision: Pandas/NumPy floating-point conversion can round large integers and high-precision decimals or overflow extreme values. Display rounding to six significant digits does not imply measurement precision. Native JSON strings are never coerced into numeric measurements.
- Nonfinite numeric values (NaN and positive/negative infinity) are excluded from numeric statistics and outlier fences; excluded counts are reported and nonfinite values are flagged by quality checks when retained as numeric input. Configured NaN text markers are missing instead. Nonfinite or unavailable summary results are displayed as N/A; category values may explicitly show +Infinity, -Infinity or NaN.
- Potential outliers: x < Q1 - 1.5 × IQR or x > Q3 + 1.5 × IQR, using finite values, linear quartiles and strict inequalities. IQR is Q3 - Q1. The check is skipped for zero IQR or fewer than 4 finite values. Skewed or multimodal distributions may naturally produce flagged values; potential outliers are not confirmed errors.
- Summary statistics include duplicate rows; distinct counts and frequencies exclude missing values. No rows are repaired, removed or imputed, and the source file is never modified.
- Scope: UTF-8 comma-separated CSV with a header, or a JSON array of flat objects. The full dataset is loaded and processed in memory, not streamed; large inputs may exhaust memory. No nested JSON, JSON Lines, date inference, plots or domain validation are provided.
- Automated checks do not establish scientific validity, physical plausibility, causal conclusions or fitness for a particular analysis. No findings does not prove the data are clean; review collection methods, units, domain constraints and downstream assumptions separately.
