# Data Inspection Report

*Researcher-centric investigation of structures_with_issues.json*

## Overview

This JSON dataset contains **21 records** across **11 variables** (2 integer, 1 mixed, 6 number, 2 string). It uses 7,434 bytes (7.25977 KiB) on disk and about 20,405 bytes (19.9268 KiB) in the profiled DataFrame.

| First-page summary | Evidence |
| --- | --- |
| Overall completeness | 97.8355% (5 missing cells across 1 variables) |
| Exact duplicate records | 1 additional occurrence(s) beyond the first |
| Identifier-like variables | 1 |
| Review findings | 11 |

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

### Priority observations

- **Duplicate rows**: 1 repeated row(s) beyond the first occurrence.
- **High missingness** in **lattice_volume**: 5 missing of 21 values (23.81%).
- **Mixed value types** in **lattice_volume**: Observed number: 15, string: 1. Representative unexpected values: \['not measured'\].
- **Potential numerical outliers** in **lattice_a**: 4/21 finite numeric values outside IQR fences \[0.674231, 11.6106\]. Examples: 13.4622, 14.1533, 612.67.
- **Potential numerical outliers** in **lattice_alpha**: 2/21 finite numeric values outside IQR fences \[33.6311, 123.821\]. Examples: 30.3091, 17.2597.

Initial assessment: the source was profiled without changing values. These are investigation prompts, not automatic corrections or scientific validation.

## Overall summary

- Missing cells: 5 across 1 column(s).
- Additional duplicate rows: 1.
- Potential quality findings: 11.
- Findings by severity: info: 8, warning: 3.

## Schema inventory

### Chapter 1: Understanding what is in the dataset

The schema comprises 2 integer, 1 mixed, 6 number, 2 string. 1 variable(s) are identifier-like and are not interpreted as measurements. Observed scalar types show the evidence used for inference.

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

| Variable | Type | Non-null | Distinct | Note |
| --- | --- | --- | --- | --- |
| material_id | string | 21 | 20 | Identifier-like |
| lattice_a | number | 21 | 20 |  |
| lattice_b | number | 21 | 20 |  |
| lattice_c | number | 21 | 20 |  |
| lattice_alpha | number | 21 | 12 |  |
| lattice_beta | number | 21 | 11 |  |
| lattice_gamma | number | 21 | 13 |  |
| num_sites | integer | 21 | 15 |  |
| num_distinct_elements | integer | 21 | 3 |  |
| elements | string | 21 | 20 |  |
| lattice_volume | mixed | 16 | 15 |  |

## Missing values

### Chapter 2: Can I rely on the completeness of this data?

Overall completeness is **97.8355%**. Missingness affects 1 variable(s). High missingness means at least 5% missing.

Most affected variables: **lattice_volume** 5 (23.8095%).

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

![Columns ranked by the number of missing records.](../assets/structures_with_issues_20261117T091950Z_e462bed6/missingness.png)

*Columns ranked by the number of missing records.*

![Distribution of missing-cell burden across records.](../assets/structures_with_issues_20261117T091950Z_e462bed6/row_missingness.png)

*Distribution of missing-cell burden across records.*

## Duplicate rows

The count is additional full-row occurrences beyond the first occurrence in each group after missing-value normalization; for example, three identical rows contribute two additional rows.

| Metric | Value |
| --- | --- |
| Additional duplicate rows | 1 |
| Share of all rows | 4.7619% |

## Numeric summaries

### Chapter 3: What do the measurements tell us?

Finite numeric values are summarized with linear quartiles and sample standard deviation (ddof=1). Mixed columns describe their numeric subset only.

- **lattice_a**: range 3.87458 to 612.67, median 6.31483, skewness 2.97337.
- **lattice_beta**: range 17.2597 to 111.295, median 90, skewness -1.53005.
- **lattice_gamma**: range 17.2597 to 120, median 90, skewness -1.32457.
- **lattice_alpha**: range 17.2597 to 111.295, median 90, skewness -1.2855.
- **lattice_c**: range 4.27419 to 16.6939, median 8.10844, skewness 1.25323.

![Histograms for selected numerical measurements; interpret scales separately.](../assets/structures_with_issues_20261117T091950Z_e462bed6/numeric_distributions.png)

*Histograms for selected numerical measurements; interpret scales separately.*

![Selected numerical ranges; points beyond whiskers are distributional candidates, not errors.](../assets/structures_with_issues_20261117T091950Z_e462bed6/numeric_boxplots.png)

*Selected numerical ranges; points beyond whiskers are distributional candidates, not errors.*

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
| lattice_volume | 15 | 0 | 128.133 | 669.012 | 323.62 | 275.276 | 143.581 | 219.241 | 424.508 | Finite numeric values |

## Categorical summaries

### Chapter 4: Are the categorical variables consistent?

Up to 5 most frequent non-missing values are shown; likely identifiers suppress modes and top values.

- **elements**: 20 distinct values; most common is "Li, P" (2/21).
- **lattice_volume**: 15 distinct values; most common is 470.819 (2/16).

| Column | Distinct (non-missing) | Most frequent value | Frequency (non-missing) | Top values (count) | Notes |
| --- | --- | --- | --- | --- | --- |
| material_id | 20 | N/A | N/A | N/A | Likely identifier; mode and top values suppressed |
| elements | 20 | "Li, P" | 2 / 21 (9.52381%) | "Li, P" (2); "C, F, O" (1); "Nd, O, Te" (1); "Al, B, O" (1); "Bi, Co, Zr" (1) |  |
| lattice_volume | 15 | 470.819 | 2 / 16 (12.5%) | 470.819 (2); "not measured" (1); 298.112 (1); 297.479 (1); 669.012 (1) |  |

### Chapter 5: How do variables relate to one another?

- **lattice_alpha** and **lattice_beta**: Pearson 0.954491, Spearman 0.881816 across 21 complete pairs.
- **lattice_beta** and **lattice_gamma**: Pearson 0.913659, Spearman 0.831211 across 21 complete pairs.
- **num_sites** and **lattice_volume**: Pearson 0.73184, Spearman 0.873324 across 15 complete pairs.
- **lattice_alpha** and **lattice_gamma**: Pearson 0.863812, Spearman 0.765037 across 21 complete pairs.
- **lattice_a** and **lattice_b**: Pearson 0.146033, Spearman 0.645224 across 21 complete pairs.

![Pearson correlations among selected numerical variables; association is not causation.](../assets/structures_with_issues_20261117T091950Z_e462bed6/correlation_heatmap.png)

*Pearson correlations among selected numerical variables; association is not causation.*

## Data quality findings

### Chapter 6: What should concern the researcher?

### Duplicate rows

**Detected:** 1 repeated row(s) beyond the first occurrence.

**Rule:** Full-row equality after missing-value normalization; count additional occurrences only.

**Why investigate:** Check whether repeated records are intended replicates before removing anything.

### High missingness — lattice_volume

**Detected:** 5 missing of 21 values (23.81%).

**Rule:** High missingness when missing fraction &gt;= 5.0%; any missing values are reported.

**Why investigate:** Review collection coverage before relying on this column; no imputation has been performed.

### Mixed value types — lattice_volume

**Detected:** Observed number: 15, string: 1. Representative unexpected values: \['not measured'\].

**Rule:** Incompatible JSON native types, or CSV numeric proportion &gt;= 80% with nonnumeric tokens; boolean/number mixtures are incompatible.

**Why investigate:** Review unexpected values or inconsistent encoding. Mixed codes can be intentional, not confirmed errors.

### Potential numerical outliers — lattice_a

**Detected:** 4/21 finite numeric values outside IQR fences \[0.674231, 11.6106\]. Examples: 13.4622, 14.1533, 612.67.

**Rule:** x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities.

**Why investigate:** Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them.

### Potential numerical outliers — lattice_alpha

**Detected:** 2/21 finite numeric values outside IQR fences \[33.6311, 123.821\]. Examples: 30.3091, 17.2597.

**Rule:** x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities.

**Why investigate:** Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them.

### Potential numerical outliers — lattice_b

**Detected:** 1/21 finite numeric values outside IQR fences \[0.654785, 12.5333\]. Examples: 14.1533.

**Rule:** x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities.

**Why investigate:** Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them.

### Potential numerical outliers — lattice_c

**Detected:** 2/21 finite numeric values outside IQR fences \[3.19415, 13.1717\]. Examples: 16.6939, 14.1533.

**Rule:** x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities.

**Why investigate:** Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them.

### Potential numerical outliers — lattice_gamma

**Detected:** 9/21 finite numeric values outside IQR fences \[82.6092, 102.318\]. Examples: 110.754, 60, 60, 60, 109.471.

**Rule:** x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities.

**Why investigate:** Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them.

### Potential numerical outliers — num_sites

**Detected:** 1/21 finite numeric values outside IQR fences \[-17.5, 50.5\]. Examples: 56.

**Rule:** x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities.

**Why investigate:** Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them.

### Strong numerical correlation — lattice_alpha ↔ lattice_beta

**Detected:** Pearson=0.954, Spearman=0.882, based on 21 complete pair(s).

**Rule:** Absolute Pearson or Spearman correlation &gt;= 0.90.

**Why investigate:** The variables may be redundant or related; correlation does not establish causation.

### Strong numerical correlation — lattice_beta ↔ lattice_gamma

**Detected:** Pearson=0.914, Spearman=0.831, based on 21 complete pair(s).

**Rule:** Absolute Pearson or Spearman correlation &gt;= 0.90.

**Why investigate:** The variables may be redundant or related; correlation does not establish causation.

| Check name | Column | Severity | Evidence | Rule | Explanation |
| --- | --- | --- | --- | --- | --- |
| Duplicate rows | (whole dataset) | warning | 1 repeated row(s) beyond the first occurrence. | Full-row equality after missing-value normalization; count additional occurrences only. | Check whether repeated records are intended replicates before removing anything. |
| High missingness | lattice_volume | warning | 5 missing of 21 values (23.81%). | High missingness when missing fraction &gt;= 5.0%; any missing values are reported. | Review collection coverage before relying on this column; no imputation has been performed. |
| Mixed value types | lattice_volume | warning | Observed number: 15, string: 1. Representative unexpected values: \['not measured'\]. | Incompatible JSON native types, or CSV numeric proportion &gt;= 80% with nonnumeric tokens; boolean/number mixtures are incompatible. | Review unexpected values or inconsistent encoding. Mixed codes can be intentional, not confirmed errors. |
| Potential numerical outliers | lattice_a | info | 4/21 finite numeric values outside IQR fences \[0.674231, 11.6106\]. Examples: 13.4622, 14.1533, 612.67. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Potential numerical outliers | lattice_alpha | info | 2/21 finite numeric values outside IQR fences \[33.6311, 123.821\]. Examples: 30.3091, 17.2597. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Potential numerical outliers | lattice_b | info | 1/21 finite numeric values outside IQR fences \[0.654785, 12.5333\]. Examples: 14.1533. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Potential numerical outliers | lattice_c | info | 2/21 finite numeric values outside IQR fences \[3.19415, 13.1717\]. Examples: 16.6939, 14.1533. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Potential numerical outliers | lattice_gamma | info | 9/21 finite numeric values outside IQR fences \[82.6092, 102.318\]. Examples: 110.754, 60, 60, 60, 109.471. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Potential numerical outliers | num_sites | info | 1/21 finite numeric values outside IQR fences \[-17.5, 50.5\]. Examples: 56. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. | Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them. |
| Strong numerical correlation | lattice_alpha ↔ lattice_beta | info | Pearson=0.954, Spearman=0.882, based on 21 complete pair(s). | Absolute Pearson or Spearman correlation &gt;= 0.90. | The variables may be redundant or related; correlation does not establish causation. |
| Strong numerical correlation | lattice_beta ↔ lattice_gamma | info | Pearson=0.914, Spearman=0.831, based on 21 complete pair(s). | Absolute Pearson or Spearman correlation &gt;= 0.90. | The variables may be redundant or related; correlation does not establish causation. |

### Chapter 7: Recommended next investigations

- Trace missing fields to collection or export steps before selecting a treatment; distinguish unavailable measurements from not-applicable values.
- Review extreme observations and zeros against source records and units; decide whether they are valid measurements, censoring, or coding conventions.
- Inspect raw categorical labels before grouping them, and preserve an auditable normalization map if one is justified.
- Check repeated records and strongly aligned variables against the study design before removing rows or selecting predictors.

## Rules and limitations

### Chapter 8: Methodology and limitations

Missing strings are normalized using configured trimmed, case-insensitive markers; JSON null and absent keys are missing. Numerical summaries use finite float64 values, linear quartiles and sample standard deviation. IQR alerts use strict fences; Pearson and Spearman associations use complete pairs. The tool processes the full file in memory.

Configured rules: missing fraction >= 5%; CSV mixed inference requires at least 80% numeric values; potential outliers use Q1 - 1.5 × IQR and Q3 + 1.5 × IQR and are skipped for zero IQR or fewer than 4 finite values. Pandas/NumPy floating-point calculations can round large integers. JSON preserves native types: quoted numbers and booleans remain strings. Nonfinite values are flagged and excluded from numeric statistics and outlier fences.

Statistical observations are not errors by themselves. This tool does not validate units, study design, causality, scientific plausibility, no domain schema, nested JSON or JSON Lines. Input is processed in memory, not streamed, and the source file is never modified.

### Technical appendix

#### Complete schema inventory

| Variable | Type | Non-null | Distinct | Observed values | Identifier-like |
| --- | --- | --- | --- | --- | --- |
| material_id | string | 21 | 20 | string: 21 | Yes |
| lattice_a | number | 21 | 20 | number: 21 | No |
| lattice_b | number | 21 | 20 | number: 21 | No |
| lattice_c | number | 21 | 20 | number: 21 | No |
| lattice_alpha | number | 21 | 12 | number: 21 | No |
| lattice_beta | number | 21 | 11 | number: 21 | No |
| lattice_gamma | number | 21 | 13 | number: 21 | No |
| num_sites | integer | 21 | 15 | integer: 21 | No |
| num_distinct_elements | integer | 21 | 3 | integer: 21 | No |
| elements | string | 21 | 20 | string: 21 | No |
| lattice_volume | mixed | 16 | 15 | number: 15, string: 1 | No |

#### Numerical statistics appendix

| Variable | Finite | Min | Max | Mean | Median | Std | Variance | Q1 | Q3 | Skew | Kurtosis | Zeros |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lattice_a | 21 | 3.87458 | 612.67 | 64.3686 | 6.31483 | 182.306 | 33235.4 | 4.77535 | 7.50944 | 2.97337 | 7.55756 | 0 (0%) |
| lattice_b | 21 | 4.26464 | 14.1533 | 7.05747 | 7.0268 | 2.46817 | 6.09188 | 5.10925 | 8.07888 | 1.23947 | 2.19137 | 0 (0%) |
| lattice_c | 21 | 4.27419 | 16.6939 | 8.33355 | 8.10844 | 2.94537 | 8.67523 | 6.93571 | 9.43009 | 1.25323 | 2.64581 | 0 (0%) |
| lattice_alpha | 21 | 17.2597 | 111.295 | 81.0827 | 90 | 24.3048 | 590.721 | 67.4524 | 90 | -1.2855 | 1.57172 | 0 (0%) |
| lattice_beta | 21 | 17.2597 | 111.295 | 83.8425 | 90 | 22.1282 | 489.656 | 90 | 90 | -1.53005 | 2.96344 | 0 (0%) |
| lattice_gamma | 21 | 17.2597 | 120 | 85.7445 | 90 | 23.2291 | 539.59 | 90 | 94.9272 | -1.32457 | 2.60539 | 0 (0%) |
| num_sites | 21 | 3 | 56 | 19.3333 | 20 | 13.4957 | 182.133 | 8 | 25 | 0.896921 | 1.09501 | 0 (0%) |
| num_distinct_elements | 21 | 2 | 4 | 2.66667 | 3 | 0.658281 | 0.433333 | 2 | 3 | 0.473568 | -0.55123 | 0 (0%) |
| lattice_volume | 15 | 128.133 | 669.012 | 323.62 | 275.276 | 143.581 | 20615.5 | 219.241 | 424.508 | 1.08736 | 0.860536 | 0 (0%) |

#### Detailed quality evidence

| Check | Location | Severity | Evidence | Rule |
| --- | --- | --- | --- | --- |
| Duplicate rows | Dataset | warning | 1 repeated row(s) beyond the first occurrence. | Full-row equality after missing-value normalization; count additional occurrences only. |
| High missingness | lattice_volume | warning | 5 missing of 21 values (23.81%). | High missingness when missing fraction &gt;= 5.0%; any missing values are reported. |
| Mixed value types | lattice_volume | warning | Observed number: 15, string: 1. Representative unexpected values: \['not measured'\]. | Incompatible JSON native types, or CSV numeric proportion &gt;= 80% with nonnumeric tokens; boolean/number mixtures are incompatible. |
| Potential numerical outliers | lattice_a | info | 4/21 finite numeric values outside IQR fences \[0.674231, 11.6106\]. Examples: 13.4622, 14.1533, 612.67. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. |
| Potential numerical outliers | lattice_alpha | info | 2/21 finite numeric values outside IQR fences \[33.6311, 123.821\]. Examples: 30.3091, 17.2597. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. |
| Potential numerical outliers | lattice_b | info | 1/21 finite numeric values outside IQR fences \[0.654785, 12.5333\]. Examples: 14.1533. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. |
| Potential numerical outliers | lattice_c | info | 2/21 finite numeric values outside IQR fences \[3.19415, 13.1717\]. Examples: 16.6939, 14.1533. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. |
| Potential numerical outliers | lattice_gamma | info | 9/21 finite numeric values outside IQR fences \[82.6092, 102.318\]. Examples: 110.754, 60, 60, 60, 109.471. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. |
| Potential numerical outliers | num_sites | info | 1/21 finite numeric values outside IQR fences \[-17.5, 50.5\]. Examples: 56. | x &lt; Q1 - 1.5 × IQR or x &gt; Q3 + 1.5 × IQR; linear quartiles, strict inequalities. |
| Strong numerical correlation | lattice_alpha ↔ lattice_beta | info | Pearson=0.954, Spearman=0.882, based on 21 complete pair(s). | Absolute Pearson or Spearman correlation &gt;= 0.90. |
| Strong numerical correlation | lattice_beta ↔ lattice_gamma | info | Pearson=0.914, Spearman=0.831, based on 21 complete pair(s). | Absolute Pearson or Spearman correlation &gt;= 0.90. |
