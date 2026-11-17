"""Render shared inspection results as escaped, self-contained Markdown."""

import html
import json
import math
import re
from collections import Counter
from collections.abc import Sequence
from decimal import Decimal

from ...models import ColumnSummary, Inspection, Scalar

__all__ = ["render_report"]

NA = "N/A"


def _escape(value: object) -> str:
    text = html.escape(str(value), quote=False).replace("\\", "\\\\")
    for character in ("`", "*", "~", "[", "]", "|"):
        text = text.replace(character, "\\" + character)
    # Intraword underscores are safe and keep ordinary column names readable.
    text = re.sub(r"(?<!\w)_|_(?!\w)", r"\\_", text)
    return (text.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> list[str]:
    return [
        "| " + " | ".join(_escape(value) for value in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(_escape(value) for value in row) + " |" for row in rows),
        "",
    ]


def _is_finite(value: float | Decimal) -> bool:
    return value.is_finite() if isinstance(value, Decimal) else math.isfinite(value)


def _number(value: float | Decimal | None) -> str:
    """Undefined or unrepresentable statistics are never printed as nan/inf."""
    return format(value, ".6g") if value is not None and _is_finite(value) else NA


def _percentage(value: float | None) -> str:
    number = _number(value * 100) if value is not None else NA
    return f"{number}%" if number != NA else NA


def _bytes(value: int | None) -> str:
    if value is None:
        return NA
    exact = f"{value:,} bytes"
    for exponent, unit in ((4, "TiB"), (3, "GiB"), (2, "MiB"), (1, "KiB")):
        if value >= 1024 ** exponent:
            return f"{exact} ({_number(value / 1024 ** exponent)} {unit})"
    return exact


def _value(value: Scalar) -> str:
    if value is None:
        return NA
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if not _is_finite(value):
        is_nan = value.is_nan() if isinstance(value, Decimal) else math.isnan(value)
        if is_nan:
            return "NaN"
        return "-Infinity" if value < 0 else "+Infinity"
    return _number(value)


def _numeric_scope(column: ColumnSummary) -> str:
    notes = []
    if column.inferred_type == "mixed" or set(column.type_counts) - {"integer", "number"}:
        notes.append("Numeric subset only; not the full column")
    else:
        notes.append("Finite numeric values")
    if column.likely_identifier:
        notes.append("Likely identifier; magnitudes may not be meaningful")
    return "; ".join(notes)


def _categorical_row(column: ColumnSummary, limit: int) -> list[object]:
    if column.likely_identifier:
        return [column.name, f"{column.distinct_count:,}", NA, NA, NA,
                "Likely identifier; mode and top values suppressed"]
    top = column.top_values[:limit]
    if top:
        mode, count = top[0]
        frequency = (
            f"{count:,} / {column.non_null_count:,} ({_percentage(count / column.non_null_count)})"
            if column.non_null_count else NA
        )
        values = "; ".join(f"{_value(value)} ({count:,})" for value, count in top)
    else:
        mode, frequency, values = None, NA, NA
    return [column.name, f"{column.distinct_count:,}", _value(mode), frequency, values, ""]


def render_report(inspection: Inspection) -> str:
    """Render a profile without reading files, recomputing statistics or mutating it."""
    dataset = inspection.dataset
    config = inspection.config
    row_count = len(dataset.rows)
    lines = ["# Data Inspection Report", "", "## Overview", ""]
    lines += _table(["Metric", "Value"], [
        ["Source file", dataset.source.name],
        ["Source path", str(dataset.source)],
        ["Extension", dataset.source.suffix or NA],
        ["Format", dataset.format],
        ["File size", _bytes(inspection.file_size_bytes)],
        ["Rows", f"{row_count:,}"],
        ["Columns", f"{len(dataset.columns):,}"],
        ["Estimated in-memory size", _bytes(inspection.memory_bytes)],
    ])
    lines += ["Memory is the reported data-memory estimate, not peak process memory.", "",
              "## Overall summary", ""]
    missing_cells = sum(column.missing_count for column in inspection.columns)
    missing_columns = sum(column.missing_count > 0 for column in inspection.columns)
    severities = Counter(finding.severity for finding in inspection.findings)
    lines += [
        f"- Missing cells: {missing_cells:,} across {missing_columns:,} column(s).",
        f"- Additional duplicate rows: {inspection.duplicate_rows:,}.",
        f"- Potential quality findings: {len(inspection.findings):,}.",
    ]
    if severities:
        lines += ["- Findings by severity: " + ", ".join(
            f"{_escape(severity)}: {count:,}" for severity, count in sorted(severities.items())
        ) + "."]
    else:
        lines += ["- No potential issues detected by the configured rules. This does not guarantee clean data."]
    lines += ["", "Findings are review prompts, not proof of invalid data or scientific validity.", "",
              "## Schema inventory", "",
              ("Non-null counts are after missing-value normalization. Inferred semantic types describe how columns "
               "are interpreted; observed scalar types show the evidence used for inference."), ""]
    lines += _table(["Column", "Non-null", "Inferred semantic type", "Observed types (count)", "Likely identifier"], [
        [column.name, f"{column.non_null_count:,}", column.inferred_type,
         ", ".join(f"{kind}: {count:,}" for kind, count in sorted(column.type_counts.items())) or NA,
         "Yes" if column.likely_identifier else "No"]
        for column in inspection.columns
    ])

    lines += ["## Missing values", "",
              f"All columns are listed. High missingness means at least {_percentage(config.missing_threshold)} missing.", ""]
    lines += _table(["Column", "Missing", "Missing %", "Non-null", "High missingness"], [
        [column.name, f"{column.missing_count:,}",
         _percentage(column.missing_fraction if row_count else None), f"{column.non_null_count:,}",
         "Yes" if column.missing_count and column.missing_fraction >= config.missing_threshold else "No"]
        for column in inspection.columns
    ])

    lines += ["## Duplicate rows", "",
              ("The count is additional full-row occurrences beyond the first occurrence in each group, "
               "after missing-value normalization; it is not the number of all rows belonging to duplicate groups. "
               "For example, three identical rows contribute two additional rows."), ""]
    lines += _table(["Metric", "Value"], [
        ["Additional duplicate rows", f"{inspection.duplicate_rows:,}"],
        ["Share of all rows", _percentage(inspection.duplicate_rows / row_count if row_count else None)],
    ])
    if not inspection.duplicate_rows:
        lines += ["No additional duplicate rows were detected under this comparison rule.", ""]

    lines += ["## Numeric summaries", "",
              ("Statistics use only the finite numeric subset, excluding missing values, text, booleans and "
               "nonfinite values. Mixed-column statistics describe the numeric subset only, not the full column. "
               "Counts include duplicate rows. Standard deviation is the sample standard deviation (ddof=1); "
               "it is undefined for fewer than two finite values. Quartiles use linear interpolation. "
               "Numbers are shown to six significant digits; N/A means undefined or unavailable."), ""]
    numeric_rows = []
    for column in inspection.columns:
        numeric = column.numeric
        if numeric is not None:
            numeric_rows.append([
                column.name, f"{numeric.count:,}", f"{numeric.nonfinite_count:,}",
                _number(numeric.minimum), _number(numeric.maximum), _number(numeric.mean),
                _number(numeric.median), _number(numeric.std), _number(numeric.q1), _number(numeric.q3),
                _numeric_scope(column),
            ])
    if numeric_rows:
        lines += _table(["Column", "Finite count", "Nonfinite excluded", "Minimum", "Maximum", "Mean",
                         "Median", "Sample std (ddof=1)", "Q1 (25%)", "Q3 (75%)", "Scope / notes"], numeric_rows)
    else:
        lines += ["No numeric values to summarize.", ""]

    lines += ["## Categorical summaries", "",
              (f"String, boolean and mixed columns, plus likely identifiers of any type. Up to {config.top_values} "
               "most frequent non-missing values are shown. Frequency uses the non-null count as denominator; "
               "ties retain first-seen order, so the displayed most frequent value need not be a unique mode. "
               "Strings are quoted to distinguish them from numbers. Likely identifiers, including numeric IDs, "
               "have their mode and top values suppressed to avoid misleading categorical interpretations."), ""]
    categorical_rows = [
        _categorical_row(column, config.top_values) for column in inspection.columns
        if column.inferred_type in {"string", "boolean", "mixed"} or column.likely_identifier
    ]
    if categorical_rows:
        lines += _table(["Column", "Distinct (non-missing)", "Most frequent value", "Frequency (non-missing)",
                         "Top values (count)", "Notes"], categorical_rows)
    else:
        lines += ["No categorical values to summarize.", ""]

    lines += ["## Data quality findings", "",
              "Each finding preserves its check name, column, severity, evidence, rule and explanation.", ""]
    if inspection.findings:
        lines += _table(["Check name", "Column", "Severity", "Evidence", "Rule", "Explanation"], [
            [finding.check_name, finding.column if finding.column is not None else "(whole dataset)",
             finding.severity, finding.evidence, finding.rule, finding.explanation]
            for finding in inspection.findings
        ])
    else:
        lines += ["No potential issues detected by the configured rules. This does not guarantee clean data.", ""]

    markers = ", ".join(_value(value) for value in sorted(set(config.missing_values) | {""}))
    lines += ["## Rules and limitations", "",
              ("- Missingness: JSON null, absent keys and blank/whitespace-only strings are missing. "
               f"Configured text markers (case-insensitive, trimmed): {_escape(markers)}. "
               f"The high-missingness threshold is inclusive: missing fraction >= {_percentage(config.missing_threshold)}."),
              ("- Duplicates compare full rows after missing normalization. Original CSV strings otherwise remain "
               "unchanged; numeric JSON 1 and 1.0 compare equal, but boolean true and numeric 1 do not. "
               "Repeated rows may be legitimate replicates."),
              ("- Types: CSV recognizes signed integers, decimal/scientific numbers and true/false "
               "(case-insensitive). Conservative mixed-numeric CSV inference requires at least "
               f"{_percentage(config.mixed_numeric_threshold)} numeric non-missing values before treating "
               "numeric/text mixtures as mixed, and avoids flagging likely identifiers as damaged numeric data. "
               "Below that threshold such mixtures remain categorical strings. Integer and number are compatible. "
               "JSON preserves native types: quoted numbers and booleans remain strings. Entirely missing columns are empty."),
              ("- Identifier hints are heuristic, not keys or uniqueness guarantees: identifier-like names require "
               f"at least {_percentage(config.identifier_unique_ratio)} uniqueness among non-missing values; "
               f"entirely unique text columns also qualify with at least {config.identifier_min_count:,} values. "
               "Mixed categorical codes can be intentional; no domain schema, expected units or dates are inferred."),
              ("- Numeric precision: Pandas/NumPy floating-point conversion can round large integers and "
               "high-precision decimals or overflow extreme values. Display rounding to six significant digits "
               "does not imply measurement precision. Native JSON strings are never coerced into numeric measurements."),
              ("- Nonfinite numeric values (NaN and positive/negative infinity) are excluded from numeric "
               "statistics and outlier fences; excluded counts are reported and nonfinite values are flagged by "
               "quality checks when retained as numeric input. Configured NaN text markers are missing instead. "
               "Nonfinite or unavailable summary results are displayed as N/A; category values may explicitly "
               "show +Infinity, -Infinity or NaN."),
              (f"- Potential outliers: x < Q1 - {_number(config.iqr_multiplier)} × IQR or "
               f"x > Q3 + {_number(config.iqr_multiplier)} × IQR, using finite values, linear quartiles "
               "and strict inequalities. IQR is Q3 - Q1. The check is skipped for zero IQR or fewer than "
               f"{config.outlier_min_count:,} finite values. Skewed or multimodal distributions may naturally "
               "produce flagged values; potential outliers are not confirmed errors."),
              ("- Summary statistics include duplicate rows; distinct counts and frequencies exclude missing values. "
               "No rows are repaired, removed or imputed, and the source file is never modified."),
              ("- Scope: UTF-8 comma-separated CSV with a header, or a JSON array of flat objects. "
               "The full dataset is loaded and processed in memory, not streamed; large inputs may exhaust memory. "
               "No nested JSON, JSON Lines, date inference, plots or domain validation are provided."),
              ("- Automated checks do not establish scientific validity, physical plausibility, causal conclusions "
               "or fitness for a particular analysis. No findings does not prove the data are clean; review "
               "collection methods, units, domain constraints and downstream assumptions separately."), ""]
    return "\n".join(lines)
