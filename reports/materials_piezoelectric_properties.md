# Data Inspection Report

## Overview

| Metric | Value |
| --- | --- |
| Source file | materials_piezoelectric_properties.csv |
| Source path | ../JobMatchAssessment/OptionB_ExampleDatasets/materials_piezoelectric_properties.csv |
| Extension | .csv |
| Format | CSV |
| File size | 520,849 bytes (508.642 KiB) |
| Rows | 3,322 |
| Columns | 15 |
| Estimated in-memory size | 3,310,124 bytes (3.15678 MiB) |

Memory is the reported data-memory estimate, not peak process memory.

## Overall summary

- Missing cells: 34 across 6 column(s).
- Additional duplicate rows: 0.
- Potential quality findings: 14.
- Findings by severity: info: 14.

Findings are review prompts, not proof of invalid data or scientific validity.

## Schema inventory

Non-null counts are after missing-value normalization. Inferred semantic types describe how columns are interpreted; observed scalar types show the evidence used for inference.

| Column | Non-null | Inferred semantic type | Observed types (count) | Likely identifier |
| --- | --- | --- | --- | --- |
| material_id | 3,322 | string | string: 3,322 | Yes |
| formula_pretty | 3,322 | string | string: 3,322 | No |
| e_longitudinal_max | 3,322 | number | number: 3,322 | No |
| e_abs_max | 3,322 | number | number: 3,322 | No |
| band_gap | 3,316 | number | number: 3,316 | No |
| crystal_system | 3,322 | string | string: 3,322 | No |
| point_group | 3,322 | string | integer: 1,313, string: 2,009 | No |
| is_metal | 3,316 | boolean | boolean: 3,316 | No |
| formation_energy_per_atom | 3,316 | number | number: 3,316 | No |
| energy_above_hull | 3,316 | number | number: 3,316 | No |
| density | 3,322 | number | number: 3,322 | No |
| is_stable | 3,317 | boolean | boolean: 3,317 | No |
| theoretical | 3,317 | boolean | boolean: 3,317 | No |
| num_atoms_in_cell | 3,322 | integer | integer: 3,322 | No |
| num_distinct_elements | 3,322 | integer | integer: 3,322 | No |

## Missing values

All columns are listed. High missingness means at least 5% missing.

| Column | Missing | Missing % | Non-null | High missingness |
| --- | --- | --- | --- | --- |
| material_id | 0 | 0% | 3,322 | No |
| formula_pretty | 0 | 0% | 3,322 | No |
| e_longitudinal_max | 0 | 0% | 3,322 | No |
| e_abs_max | 0 | 0% | 3,322 | No |
| band_gap | 6 | 0.180614% | 3,316 | No |
| crystal_system | 0 | 0% | 3,322 | No |
| point_group | 0 | 0% | 3,322 | No |
| is_metal | 6 | 0.180614% | 3,316 | No |
| formation_energy_per_atom | 6 | 0.180614% | 3,316 | No |
| energy_above_hull | 6 | 0.180614% | 3,316 | No |
| density | 0 | 0% | 3,322 | No |
| is_stable | 5 | 0.150512% | 3,317 | No |
| theoretical | 5 | 0.150512% | 3,317 | No |
| num_atoms_in_cell | 0 | 0% | 3,322 | No |
| num_distinct_elements | 0 | 0% | 3,322 | No |

## Duplicate rows

The count is additional full-row occurrences beyond the first occurrence in each group, after missing-value normalization; it is not the number of all rows belonging to duplicate groups. For example, three identical rows contribute two additional rows.

| Metric | Value |
| --- | --- |
| Additional duplicate rows | 0 |
| Share of all rows | 0% |

No additional duplicate rows were detected under this comparison rule.

## Numeric summaries

Statistics use only the finite numeric subset, excluding missing values, text, booleans and nonfinite values. Mixed-column statistics describe the numeric subset only, not the full column. Counts include duplicate rows. Standard deviation is the sample standard deviation (ddof=1); it is undefined for fewer than two finite values. Quartiles use linear interpolation. Numbers are shown to six significant digits; N/A means undefined or unavailable.

| Column | Finite count | Nonfinite excluded | Minimum | Maximum | Mean | Median | Sample std (ddof=1) | Q1 (25%) | Q3 (75%) | Scope / notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| e_longitudinal_max | 3,322 | 0 | 0 | 91.5779 | 0.820654 | 0.317153 | 3.14961 | 0.124283 | 0.754926 | Finite numeric values |
| e_abs_max | 3,322 | 0 | 0 | 119.036 | 0.835579 | 0.332815 | 3.31699 | 0.145245 | 0.73894 | Finite numeric values |
| band_gap | 3,316 | 0 | 0 | 8.3751 | 2.47956 | 2.20635 | 1.6682 | 1.163 | 3.6265 | Finite numeric values |
| formation_energy_per_atom | 3,316 | 0 | -4.48897 | 4.6882 | -1.72703 | -1.71284 | 0.99019 | -2.52346 | -0.898324 | Finite numeric values |
| energy_above_hull | 3,316 | 0 | 0 | 4.88245 | 0.0454466 | 0.00741184 | 0.157745 | 0 | 0.0554358 | Finite numeric values |
| density | 3,322 | 0 | 0.212291 | 13.1605 | 4.10656 | 3.75548 | 1.83666 | 2.81446 | 5.04347 | Finite numeric values |
| num_atoms_in_cell | 3,322 | 0 | 2 | 288 | 22.1969 | 20 | 15.9073 | 12 | 28 | Finite numeric values |
| num_distinct_elements | 3,322 | 0 | 1 | 6 | 3.30042 | 3 | 0.799763 | 3 | 4 | Finite numeric values |

## Categorical summaries

String, boolean and mixed columns, plus likely identifiers of any type. Up to 5 most frequent non-missing values are shown. Frequency uses the non-null count as denominator; ties retain first-seen order, so the displayed most frequent value need not be a unique mode. Strings are quoted to distinguish them from numbers. Likely identifiers, including numeric IDs, have their mode and top values suppressed to avoid misleading categorical interpretations.

| Column | Distinct (non-missing) | Most frequent value | Frequency (non-missing) | Top values (count) | Notes |
| --- | --- | --- | --- | --- | --- |
| material_id | 3,322 | N/A | N/A | N/A | Likely identifier; mode and top values suppressed |
| formula_pretty | 2,817 | "SiO2" | 44 / 3,322 (1.3245%) | "SiO2" (44); "ZnS" (13); "LiMnPO4" (10); "Li4CO4" (9); "LiFeSiO4" (9) |  |
| crystal_system | 7 | "Orthorhombic" | 876 / 3,322 (26.3697%) | "Orthorhombic" (876); "Tetragonal" (586); "Monoclinic" (526); "Cubic" (391); "Trigonal" (382) |  |
| point_group | 21 | "mm2" | 641 / 3,322 (19.2956%) | "mm2" (641); "-42m" (289); "-43m" (284); "2" (270); "m" (260) |  |
| is_metal | 2 | "False" | 3,238 / 3,316 (97.6478%) | "False" (3,238); "True" (78) |  |
| is_stable | 2 | "False" | 2,050 / 3,317 (61.8028%) | "False" (2,050); "True" (1,267) |  |
| theoretical | 2 | "False" | 1,766 / 3,317 (53.2409%) | "False" (1,766); "True" (1,551) |  |

## Data quality findings

Each finding preserves its check name, column, severity, evidence, rule and explanation.

| Check name | Column | Severity | Evidence | Rule | Explanation |
| --- | --- | --- | --- | --- | --- |
| Potential numerical outliers | e_longitudinal_max | info | 273/3,322 finite numeric values outside IQR fences \[-0.821683, 1.70089\]. Examples: 7.55048, 1.79911, 2.47258, 2.74, 1.71806. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Potential numerical outliers | e_abs_max | info | 307/3,322 finite numeric values outside IQR fences \[-0.745298, 1.62948\]. Examples: 6.53956, 1.80003, 2.47331, 2.74012, 1.71795. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Missing values | band_gap | info | 6 missing of 3,322 values (0.18%). | High missingness when missing fraction &gt;= 5.0%; any missing values are reported. | Review collection coverage before relying on this column; no imputation has been performed. |
| Potential numerical outliers | band_gap | info | 13/3,316 finite numeric values outside IQR fences \[-2.53225, 7.32175\]. Examples: 8.0901, 8.3196, 7.9151, 7.56956, 8.246. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Missing values | is_metal | info | 6 missing of 3,322 values (0.18%). | High missingness when missing fraction &gt;= 5.0%; any missing values are reported. | Review collection coverage before relying on this column; no imputation has been performed. |
| Missing values | formation_energy_per_atom | info | 6 missing of 3,322 values (0.18%). | High missingness when missing fraction &gt;= 5.0%; any missing values are reported. | Review collection coverage before relying on this column; no imputation has been performed. |
| Potential numerical outliers | formation_energy_per_atom | info | 2/3,316 finite numeric values outside IQR fences \[-4.96116, 1.53938\]. Examples: 4.6882, 2.94862. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Missing values | energy_above_hull | info | 6 missing of 3,322 values (0.18%). | High missingness when missing fraction &gt;= 5.0%; any missing values are reported. | Review collection coverage before relying on this column; no imputation has been performed. |
| Potential numerical outliers | energy_above_hull | info | 213/3,316 finite numeric values outside IQR fences \[-0.0831537, 0.13859\]. Examples: 0.360776, 0.251843, 0.399725, 0.223489, 0.322402. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Potential numerical outliers | density | info | 105/3,322 finite numeric values outside IQR fences \[-0.529042, 8.38698\]. Examples: 9.70251, 8.8536, 9.33643, 13.1605, 8.89946. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Missing values | is_stable | info | 5 missing of 3,322 values (0.15%). | High missingness when missing fraction &gt;= 5.0%; any missing values are reported. | Review collection coverage before relying on this column; no imputation has been performed. |
| Missing values | theoretical | info | 5 missing of 3,322 values (0.15%). | High missingness when missing fraction &gt;= 5.0%; any missing values are reported. | Review collection coverage before relying on this column; no imputation has been performed. |
| Potential numerical outliers | num_atoms_in_cell | info | 132/3,322 finite numeric values outside IQR fences \[-12, 52\]. Examples: 56, 80, 84, 54, 64. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Potential numerical outliers | num_distinct_elements | info | 23/3,322 finite numeric values outside IQR fences \[1.5, 5.5\]. Examples: 6, 1. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |

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
