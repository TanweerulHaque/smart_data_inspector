# FG Data Profiling research notes

## Scope and licence boundary

This document records a source/documentation study of [fg-data-profiling](https://github.com/Data-Centric-AI-Community/fg-data-profiling), whose repository describes an MIT-licensed profiling package for Pandas and Spark. Its `develop` tree, README, packaging metadata, examples, source and tests were reviewed on 17 November 2026. In particular, the Pandas duplicate implementation groups full duplicate rows for a bounded display, `model/alerts.py` separates generic/type-specific/correlation alerts, and the correlation presentation ranks strongest off-diagonal pairs. Smart Data Inspector contains independent, small Pandas/NumPy/Matplotlib implementations only: it does not install, import, wrap, copy substantial implementation from, or expose either `fg-data-profiling` or `ydata-profiling`.

## Useful reference ideas adopted independently

| Reference capability | Independent decision in Smart Data Inspector | Algorithm and limitation |
| --- | --- | --- |
| Variable-type inference and overview | `profiling/schema/profiler.py` classifies native scalars, strict CSV lexical numerics/booleans, ISO-like datetimes, mixed columns, identifiers and empty fields. | Inference is heuristic; quoted JSON numerics remain text and dates are deliberately conservative. |
| Univariate description | `profiling/numeric/profiler.py` computes finite count, min/max, mean/median/mode, sample deviation/variance, linear quartiles, IQR, skewness, kurtosis and zeros. | Float64 conversion may round high-precision or extreme values; nonfinite values are reported and excluded. |
| Categorical/text exploration | Categorical frequency summaries plus `profiling/text.py` identify lengths, surrounding whitespace and case-fold collisions. | Text checks do not infer language, Unicode scripts, PII, or semantic validity. |
| Missing-data overview and alerts | `profiling/missingness*` provides per-column/row burden, repeated missing-column sets and pair co-occurrence. | Co-occurrence is descriptive only; it does not infer a missing-data mechanism. |
| Multivariate correlations | `profiling/relationships.py` estimates Pearson and Spearman correlations on finite complete pairs and `quality/relationships.py` flags threshold-exceeding associations. | Requires at least three varying complete pairs; associations are not causal and sampling is capped by configuration. |
| Alerts | Structured `Finding` values retain severity, evidence, rule and interpretation for duplicates, type conflicts, missingness, IQR candidates, constants, zeros, formatting, duplicate columns and correlation. | Rules are prompts, not data repairs or domain validation. |
| Configurable/smaller profiles | `InspectionConfig` centralises thresholds and a deterministic row cap used only for relationship calculations. | This project is an in-memory local CLI, not a Spark/distributed profiler. |
| Reproducibility information | The report states methods, thresholds and limitations; assets/reports receive unique run IDs. | No dataset-comparison UI, time-series decomposition, image/file metadata, widgets, HTML templating or sensitive-data features were recreated because they are outside the assessment and first-pass use case. |

## Design rationale

The upstream package is intentionally broad, including notebook/widget/HTML outputs, Spark support, time-series, rich text/image analyses and comparison reports. Recreating that breadth would obscure the assessment’s core question: can a researcher understand an unfamiliar local CSV or flat JSON file? This project therefore selects transparent algorithms that are easy to unit-test and explain in Markdown. In particular, IQR is used only as a potential-outlier screen, frequency/formatting checks are not corrections, and a high correlation is described as a possible redundancy rather than evidence of causation.

The remaining upstream capabilities—distributed/Spark execution, interactive HTML/widgets, file/image metadata, nonlinear categorical association, time-series decomposition, sensitive-data controls and multi-dataset comparison—are deliberate non-goals. They require heavier dependencies, a different input/workflow, or domain policy; adding them would weaken the single-file, local research-inspection product rather than complete an unfinished selected feature.

The report layout borrows the useful *progression* of overview, alerts and reproducibility—not report code or templates—and changes it into a narrative with a first-page assessment plus a technical appendix.
