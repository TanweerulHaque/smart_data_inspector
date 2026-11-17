"""Render an evidence-led Markdown investigation from computed results only."""

import html
import json
import math
import re
from collections import Counter
from collections.abc import Sequence
from decimal import Decimal

from ...models import ChartAsset, ColumnSummary, Finding, Inspection, Scalar

__all__ = ["render_report"]
NA = "N/A"


def _escape(value: object) -> str:
    text = html.escape(str(value), quote=False).replace("\\", "\\\\")
    for character in ("`", "*", "~", "[", "]", "|"):
        text = text.replace(character, "\\" + character)
    return re.sub(r"(?<!\w)_|_(?!\w)", r"\\_", text).replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> list[str]:
    return ["| " + " | ".join(_escape(item) for item in headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *("| " + " | ".join(_escape(item) for item in row) + " |" for row in rows), ""]


def _finite(value: float | Decimal | None) -> bool:
    return value is not None and (value.is_finite() if isinstance(value, Decimal) else math.isfinite(value))


def _number(value: float | Decimal | None) -> str:
    return format(value, ".6g") if _finite(value) else NA


def _percent(value: float | None) -> str:
    return f"{_number(value * 100)}%" if value is not None else NA


def _bytes(value: int | None) -> str:
    if value is None:
        return NA
    if value >= 1024 ** 2:
        return f"{value:,} bytes ({_number(value / 1024 ** 2)} MiB)"
    if value >= 1024:
        return f"{value:,} bytes ({_number(value / 1024)} KiB)"
    return f"{value:,} bytes"


def _value(value: Scalar | None) -> str:
    if value is None:
        return NA
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (float, Decimal)):
        if _finite(value):
            return _number(value)
        is_nan = value.is_nan() if isinstance(value, Decimal) else math.isnan(value)
        return "NaN" if is_nan else ("-Infinity" if value < 0 else "+Infinity")
    return str(value)


def _asset(lines: list[str], assets: list[ChartAsset], key: str) -> None:
    asset = next((item for item in assets if item.key == key), None)
    if asset:
        lines += [f"![{_escape(asset.caption)}]({_escape(asset.relative_path)})", "", f"*{_escape(asset.caption)}*", ""]


def _top(findings: list[Finding], limit: int = 5) -> list[Finding]:
    return sorted(findings, key=lambda item: ({"warning": 0, "info": 1}.get(item.severity, 2), item.check_name, item.column or ""))[:limit]


def _recommendations(inspection: Inspection) -> list[str]:
    checks = {item.check_name for item in inspection.findings}
    ideas = []
    if checks & {"High missingness", "Missing values", "All-null column"}:
        ideas.append("Trace missing fields to collection or export steps before selecting a treatment; distinguish unavailable measurements from not-applicable values.")
    if checks & {"Potential numerical outliers", "Excessive zeros"}:
        ideas.append("Review extreme observations and zeros against source records and units; decide whether they are valid measurements, censoring, or coding conventions.")
    if checks & {"Mixed value types", "Whitespace inconsistencies", "Case inconsistencies", "Rare categories"}:
        ideas.append("Inspect raw categorical labels before grouping them, and preserve an auditable normalization map if one is justified.")
    if checks & {"Potential duplicate columns", "Strong numerical correlation", "Duplicate rows"}:
        ideas.append("Check repeated records and strongly aligned variables against the study design before removing rows or selecting predictors.")
    if checks & {"Future dates", "Invalid calendar dates", "Mixed date formats"}:
        ideas.append("Standardise date/time columns to one ISO 8601 layout and timezone, and confirm future or impossible dates against the source system.")
    if checks & {"Ambiguous missing-value marker", "Missing-value markers converted"}:
        ideas.append("Confirm that converted text markers really mean 'unknown'; re-run with --missing-value or --no-missing-markers if any are legitimate codes.")
    return ideas or ["Review provenance, units, sampling frame and domain constraints; these cannot be established from a file profile alone."]


def _missingness_detail(inspection: Inspection) -> list[str]:
    """Row burden, repeated missing-column patterns, co-occurring pairs and marker conversions."""
    lines: list[str] = []
    profile = inspection.missingness
    rows = inspection.dataset.row_count
    if profile and profile.total_missing:
        burden = profile.row_missing_counts
        affected = sum(count > 0 for count in burden)
        lines += [f"Row burden: {affected:,} of {rows:,} record(s) have at least one missing cell; the worst record misses "
                  f"{max(burden):,} of {len(inspection.columns):,} fields.", ""]
        if profile.patterns:
            lines += ["#### Most common missing-value patterns", "",
                      "Each pattern is the exact set of fields missing together in a record.", ""]
            lines += _table(["Missing together", "Records", "Share of records"], [
                [", ".join(pattern.columns), f"{pattern.count:,}", _percent(pattern.count / rows if rows else None)]
                for pattern in profile.patterns])
        if profile.cooccurrences:
            left, right, count = profile.cooccurrences[0]
            lines += [f"The most common pair of absent fields is **{_escape(left)}** and **{_escape(right)}** "
                      f"({count:,} records); review their shared collection path.", "",
                      "#### Fields missing in the same records", ""]
            lines += _table(["Field A", "Field B", "Records missing both"],
                            [[left, right, f"{count:,}"] for left, right, count in profile.cooccurrences])
    converted = [column for column in inspection.columns if column.marker_conversions]
    if converted:
        lines += ["#### Text converted to missing", "",
                  "These raw values were treated as missing before profiling (\"(blank)\" = empty or whitespace-only text).", ""]
        lines += _table(["Column", "Converted values (count)", "Total converted"], [
            [column.name, "; ".join(f"{repr(token) if token else '(blank)'} ×{count:,}"
                                    for token, count in sorted(column.marker_conversions.items())),
             f"{sum(column.marker_conversions.values()):,}"] for column in converted])
    return lines


def _date_section(columns: list[ColumnSummary]) -> list[str]:
    dated = [column for column in columns if column.datetime is not None]
    if not dated:
        return []
    lines = ["## Date and time summaries", "", "### What period does the data cover?", "",
             f"Compared with the inspection time {_escape(dated[0].datetime.reference_time)} (UTC). Only ISO-like text and native "
             "date/time values are parsed; other date-looking text is counted as a non-ISO format, not guessed.", ""]
    lines += _table(["Column", "Parsed", "Earliest", "Latest", "Span (days)", "Future", "Invalid", "Formats (count)", "Timezone-aware / naive"], [
        [column.name, f"{column.datetime.count:,}", column.datetime.minimum or NA, column.datetime.maximum or NA,
         _number(column.datetime.span_days), f"{column.datetime.future_count:,}", f"{column.datetime.invalid_count:,}",
         "; ".join(f"{label}: {count:,}" for label, count in sorted(column.datetime.formats.items())),
         f"{column.datetime.timezone_aware_count:,} / {column.datetime.naive_count:,}"] for column in dated])
    return lines


def _text_section(columns: list[ColumnSummary]) -> list[str]:
    texts = [column for column in columns if column.text is not None
             and column.inferred_type in {"string", "mixed", "datetime"}]
    if not texts:
        return []
    lines = ["#### Text value summaries", "",
             "Lengths are in characters for non-missing string values; whitespace counts values with leading/trailing spaces.", ""]
    lines += _table(["Column", "Strings", "Empty", "Leading/trailing whitespace", "Case-only variants", "Min length", "Mean length", "Max length"], [
        [column.name, f"{column.text.count:,}", f"{column.text.empty_count:,}", f"{column.text.whitespace_count:,}",
         f"{column.text.casefold_collision_count:,}", column.text.minimum_length if column.text.minimum_length is not None else NA,
         _number(column.text.mean_length), column.text.maximum_length if column.text.maximum_length is not None else NA]
        for column in texts])
    return lines


def _chart_section(inspection: Inspection) -> list[str]:
    """List every chart outcome so skipped or failed charts are never silent."""
    if not inspection.chart_status:
        return []
    unavailable = [item for item in inspection.chart_status if item.status != "generated"]
    lines = ["### Chart availability", ""]
    if not unavailable:
        lines += ["All applicable charts were generated.", ""]
    lines += _table(["Chart", "Status", "Detail"], [[item.title, item.status, item.detail] for item in inspection.chart_status])
    failed = [item for item in unavailable if item.status == "failed"]
    if failed:
        lines += [f"{len(failed):,} chart(s) failed to render; the report is otherwise complete.", ""]
    return lines


def render_report(inspection: Inspection) -> str:
    """Build a layered report without file I/O, data mutation, or recalculation."""
    dataset, config, columns = inspection.dataset, inspection.config, inspection.columns
    rows = dataset.row_count
    missing = sum(column.missing_count for column in columns)
    missing_columns = sum(column.missing_count > 0 for column in columns)
    completeness = 1 - missing / (rows * len(columns)) if rows and columns else None
    kinds = Counter(column.inferred_type for column in columns)
    kind_text = ", ".join(f"{count} {kind}" for kind, count in sorted(kinds.items())) or "no variables"
    lines = ["# Data Inspection Report", "", f"*Researcher-centric investigation of {_escape(dataset.source.name)}*", "", "## Overview", "",
             (f"This {_escape(dataset.format)} dataset contains **{rows:,} records** across **{len(columns):,} variables** "
              f"({_escape(kind_text)}). It uses {_bytes(inspection.file_size_bytes)} on disk and about "
              f"{_bytes(inspection.memory_bytes)} in the profiled DataFrame."), ""]
    lines += _table(["First-page summary", "Evidence"], [
        ["Overall completeness", f"{_percent(completeness)} ({missing:,} missing cells across {missing_columns:,} variables)"],
        ["Exact duplicate records", f"{inspection.duplicate_rows:,} additional occurrence(s) beyond the first"],
        ["Identifier-like variables", f"{sum(column.likely_identifier for column in columns):,}"],
        ["Review findings", f"{len(inspection.findings):,}"],
    ])
    lines += _table(["Metric", "Value"], [
        ["Source file", dataset.source.name], ["Source path", str(dataset.source)], ["Extension", dataset.source.suffix or NA],
        ["Format", dataset.format], ["File size", _bytes(inspection.file_size_bytes)], ["Rows", f"{rows:,}"],
        ["Columns", f"{len(columns):,}"], ["Estimated in-memory size", _bytes(inspection.memory_bytes)],
    ])
    lines += ["### Priority observations", ""]
    if inspection.findings:
        for finding in _top(inspection.findings):
            location = f" in **{_escape(finding.column)}**" if finding.column else ""
            lines.append(f"- **{_escape(finding.check_name)}**{location}: {_escape(finding.evidence)}")
    else:
        lines.append("- No configured structural or statistical prompts were produced. This is not proof of fitness for a research question.")
    severity_text = ", ".join(f"{level}: {count}" for level, count in sorted(Counter(item.severity for item in inspection.findings).items()))
    lines += ["", "Initial assessment: the source was profiled without changing values. These are investigation prompts, not automatic corrections or scientific validation.", "",
              "## Overall summary", "", f"- Missing cells: {missing:,} across {missing_columns:,} column(s).", f"- Additional duplicate rows: {inspection.duplicate_rows:,}.", f"- Potential quality findings: {len(inspection.findings):,}." ]
    if severity_text:
        lines += [f"- Findings by severity: {severity_text}."]
    else:
        lines += ["- No potential issues detected by the configured rules. This does not guarantee clean data."]
    lines += ["",
              "## Schema inventory", "", "### Chapter 1: Understanding what is in the dataset", "",
              f"The schema comprises {_escape(kind_text)}. {sum(column.likely_identifier for column in columns):,} variable(s) are identifier-like and are not interpreted as measurements. Observed scalar types show the evidence used for inference.", ""]
    lines += _table(["Column", "Non-null", "Inferred semantic type", "Observed types (count)", "Likely identifier"], [
        [column.name, f"{column.non_null_count:,}", column.inferred_type,
         ", ".join(f"{name}: {count:,}" for name, count in sorted(column.type_counts.items())) or NA,
         "Yes" if column.likely_identifier else "No"] for column in columns
    ])
    lines += _table(["Variable", "Type", "Non-null", "Distinct", "Note"], [
        [column.name, column.inferred_type, f"{column.non_null_count:,}", f"{column.distinct_count:,}",
         "Identifier-like" if column.likely_identifier else ("All missing" if column.inferred_type == "empty" else "")]
        for column in columns[:20]
    ])
    if len(columns) > 20:
        lines += [f"The appendix lists all {len(columns):,} variables.", ""]
    lines += ["## Missing values", "", "### Chapter 2: Can I rely on the completeness of this data?", "",
              f"Overall completeness is **{_percent(completeness)}**. " + (f"Missingness affects {missing_columns:,} variable(s)." if missing_columns else "No missing cells remain after configured marker normalization.") + f" High missingness means at least {_percent(config.missing_threshold)} missing.", ""]
    ranked = sorted((column for column in columns if column.missing_count), key=lambda item: item.missing_count, reverse=True)
    if ranked:
        lines += ["Most affected variables: " + "; ".join(f"**{_escape(column.name)}** {column.missing_count:,} ({_percent(column.missing_fraction)})" for column in ranked[:5]) + ".", ""]
    lines += _table(["Column", "Missing", "Missing %", "Non-null", "High missingness"], [
        [column.name, f"{column.missing_count:,}", _percent(column.missing_fraction if rows else None), f"{column.non_null_count:,}",
         "Yes" if column.missing_count and column.missing_fraction >= config.missing_threshold else "No"] for column in columns
    ])
    if inspection.missingness and inspection.missingness.high_missing_rows:
        lines += [f"{inspection.missingness.high_missing_rows:,} record(s) have at least {_percent(config.row_missing_threshold)} of fields missing.", ""]
    lines += _missingness_detail(inspection)
    _asset(lines, inspection.assets, "missingness")
    _asset(lines, inspection.assets, "row_missingness")
    lines += ["## Duplicate rows", "", "The count is additional full-row occurrences beyond the first occurrence in each group after missing-value normalization; for example, three identical rows contribute two additional rows.", ""]
    lines += _table(["Metric", "Value"], [["Additional duplicate rows", f"{inspection.duplicate_rows:,}"], ["Share of all rows", _percent(inspection.duplicate_rows / rows if rows else None)]])
    numeric = [column for column in columns if column.numeric is not None and not column.likely_identifier]
    lines += ["## Numeric summaries", "", "### Chapter 3: What do the measurements tell us?", "", "Finite numeric values are summarized with linear quartiles and sample standard deviation (ddof=1). Mixed columns describe their numeric subset only.", ""]
    if numeric:
        selected = sorted(numeric, key=lambda item: max(abs(item.numeric.skewness or 0), item.numeric.zero_fraction), reverse=True)[:5]
        for column in selected:
            summary = column.numeric
            assert summary is not None
            shape = f"skewness {_number(summary.skewness)}" if summary.skewness is not None else "distribution shape unavailable for this sample size"
            zero_note = f" Zeros: {_percent(summary.zero_fraction)}." if summary.zero_count else ""
            lines.append(f"- **{_escape(column.name)}**: range {_number(summary.minimum)} to {_number(summary.maximum)}, median {_number(summary.median)}, {shape}.{zero_note}")
        lines.append("")
        _asset(lines, inspection.assets, "numeric_distributions")
        _asset(lines, inspection.assets, "numeric_boxplots")
    else:
        lines += ["No non-identifier numerical variables had finite values suitable for this narrative. No numeric values to summarize.", ""]
    lines += _table(["Column", "Finite count", "Nonfinite excluded", "Minimum", "Maximum", "Mean", "Median", "Sample std (ddof=1)", "Q1 (25%)", "Q3 (75%)", "Mode", "Zero share", "Scope / notes"], [
        [column.name, f"{column.numeric.count:,}", f"{column.numeric.nonfinite_count:,}", _number(column.numeric.minimum), _number(column.numeric.maximum), _number(column.numeric.mean), _number(column.numeric.median), _number(column.numeric.std), _number(column.numeric.q1), _number(column.numeric.q3), _number(column.numeric.mode), _percent(column.numeric.zero_fraction), "Likely identifier" if column.likely_identifier else "Finite numeric values"] for column in columns if column.numeric is not None
    ])
    lines += _date_section(columns)
    categorical = [column for column in columns if column.inferred_type in {"string", "boolean", "mixed"} and not column.likely_identifier]
    lines += ["## Categorical summaries", "", "### Chapter 4: Are the categorical variables consistent?", "", f"Up to {config.top_values} most frequent non-missing values are shown; likely identifiers suppress modes and top values.", ""]
    if categorical:
        for column in categorical[:5]:
            if column.top_values:
                value, count = column.top_values[0]
                lines.append(f"- **{_escape(column.name)}**: {column.distinct_count:,} distinct values; most common is {_escape(_value(value))} ({count:,}/{column.non_null_count:,}).")
        lines.append("")
        _asset(lines, inspection.assets, "categories")
    else:
        lines += ["No non-identifier categorical variables were available for review.", ""]
    lines += _table(["Column", "Distinct (non-missing)", "Most frequent value", "Frequency (non-missing)", "Top values (count)", "Notes"], [
        [column.name, f"{column.distinct_count:,}", _value(column.top_values[0][0]) if column.top_values and not column.likely_identifier else NA,
         f"{column.top_values[0][1]:,} / {column.non_null_count:,} ({_percent(column.top_values[0][1] / column.non_null_count)})" if column.top_values and column.non_null_count and not column.likely_identifier else NA,
         "; ".join(f"{_value(value)} ({count:,})" for value, count in column.top_values) if not column.likely_identifier else NA,
         "Likely identifier; mode and top values suppressed" if column.likely_identifier else ""]
        for column in columns if column.inferred_type in {"string", "boolean", "mixed"} or column.likely_identifier
    ])
    lines += _text_section(columns)
    pairs = inspection.relationships.relationships if inspection.relationships else []
    lines += ["### Chapter 5: How do variables relate to one another?", ""]
    if pairs:
        for pair in pairs[:5]:
            lines.append(f"- **{_escape(pair.left)}** and **{_escape(pair.right)}**: Pearson {_number(pair.pearson)}, Spearman {_number(pair.spearman)} across {pair.pair_count:,} complete pairs.")
        lines.append("")
        _asset(lines, inspection.assets, "correlations")
    else:
        lines += ["There were not enough varying numerical variables with complete pairs to estimate correlations.", ""]
    lines += ["## Data quality findings", "", "### Chapter 6: What should concern the researcher?", ""]
    if inspection.findings:
        for finding in _top(inspection.findings, 12):
            location = f" — {_escape(finding.column)}" if finding.column else ""
            lines += [f"### {_escape(finding.check_name)}{location}", "", f"**Detected:** {_escape(finding.evidence)}", "", f"**Rule:** {_escape(finding.rule)}", "", f"**Why investigate:** {_escape(finding.explanation)}", ""]
    else:
        lines += ["No configured alerts need prioritisation. No potential issues detected by the configured rules. This does not guarantee clean data.", ""]
    lines += _table(["Check name", "Column", "Severity", "Evidence", "Rule", "Explanation"], [[item.check_name, item.column or "(whole dataset)", item.severity, item.evidence, item.rule, item.explanation] for item in inspection.findings])
    lines += ["### Chapter 7: Recommended next investigations", "", *(f"- {idea}" for idea in _recommendations(inspection)), "",
              "## Rules and limitations", "", "### Chapter 8: Methodology and limitations", "",
              f"Missing strings are normalized only when the trimmed text exactly (case-sensitively) equals a configured marker ({_escape(', '.join(repr(item) for item in config.missing_values if item)) or 'blank text only'}); blanks, JSON null and absent keys are always missing, and every conversion is counted per column. ISO-like date text and native date/time values are summarised; naive times are compared as UTC. Numerical summaries use finite float64 values, linear quartiles and sample standard deviation. IQR alerts use strict fences; Pearson and Spearman associations use complete pairs. The tool processes the full file in memory.", "",
              f"Configured rules: missing fraction >= {_percent(config.missing_threshold)}; CSV mixed inference requires at least {_percent(config.mixed_numeric_threshold)} numeric values; potential outliers use Q1 - {_number(config.iqr_multiplier)} × IQR and Q3 + {_number(config.iqr_multiplier)} × IQR and are skipped for zero IQR or fewer than {config.outlier_min_count} finite values. Pandas/NumPy floating-point calculations can round large integers. JSON preserves native types: quoted numbers and booleans remain strings. Nonfinite values are flagged and excluded from numeric statistics and outlier fences.", "",
              "Statistical observations are not errors by themselves. This tool does not validate units, study design, causality, scientific plausibility, no domain schema, nested JSON or JSON Lines. Input is processed in memory, not streamed, and the source file is never modified.", "",
              *_chart_section(inspection),
              "### Technical appendix", "", "#### Complete schema inventory", ""]
    lines += _table(["Variable", "Type", "Non-null", "Distinct", "Observed values", "Identifier-like"], [
        [column.name, column.inferred_type, f"{column.non_null_count:,}", f"{column.distinct_count:,}",
         ", ".join(f"{name}: {count:,}" for name, count in sorted(column.type_counts.items())) or NA,
         "Yes" if column.likely_identifier else "No"] for column in columns
    ])
    lines += ["#### Numerical statistics appendix", ""]
    all_numeric = [column for column in columns if column.numeric is not None]
    if all_numeric:
        lines += _table(["Variable", "Finite", "Min", "Max", "Mean", "Median", "Mode", "Std", "Variance", "Q1", "Q3", "Skew", "Kurtosis", "Zeros"], [
            [column.name, f"{column.numeric.count:,}", _number(column.numeric.minimum), _number(column.numeric.maximum), _number(column.numeric.mean), _number(column.numeric.median), _number(column.numeric.mode), _number(column.numeric.std), _number(column.numeric.variance), _number(column.numeric.q1), _number(column.numeric.q3), _number(column.numeric.skewness), _number(column.numeric.kurtosis), f"{column.numeric.zero_count:,} ({_percent(column.numeric.zero_fraction)})"]
            for column in all_numeric
        ])
    else:
        lines += ["No numerical summaries are available.", ""]
    lines += ["#### Detailed quality evidence", ""]
    if inspection.findings:
        lines += _table(["Check", "Location", "Severity", "Evidence", "Rule"], [[item.check_name, item.column or "Dataset", item.severity, item.evidence, item.rule] for item in inspection.findings])
    else:
        lines += ["No configured quality findings.", ""]
    return "\n".join(lines)
