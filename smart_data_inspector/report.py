"""Render inspection results as a self-contained Markdown report."""

import html
import json
import re
from collections.abc import Sequence
from decimal import Decimal

from .inspector import Inspection
from .loaders import Scalar


def _escape(value: object) -> str:
    text = html.escape(str(value), quote=False).replace("\\", "\\\\")
    for character in ("`", "*", "[", "]", "|"):
        text = text.replace(character, "\\" + character)
    # Intraword underscores are safe in Markdown and keep column names readable.
    text = re.sub(r"(?<!\w)_|_(?!\w)", r"\\_", text)
    return text.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> list[str]:
    return [
        "| " + " | ".join(_escape(value) for value in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(_escape(value) for value in row) + " |" for row in rows),
        "",
    ]


def _number(value: Decimal) -> str:
    return format(value, ".6g")


def _value(value: Scalar) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def render_report(inspection: Inspection) -> str:
    """Escape user-provided text so it cannot add Markdown rows or headings."""
    dataset = inspection.dataset
    config = inspection.config
    lines = ["# Data Inspection Report", "", "## Overview", ""]
    lines += _table(["Metric", "Value"], [
        ["Source", str(dataset.source)],
        ["Format", dataset.format],
        ["Rows", f"{len(dataset.rows):,}"],
        ["Columns", len(dataset.columns)],
        ["Duplicate rows (beyond first)", f"{inspection.duplicate_rows:,}"],
        ["Potential quality findings", len(inspection.findings)],
    ])
    lines += ["## Data quality findings", "", "These are review prompts, not proof of invalid data.", ""]
    if inspection.findings:
        lines += _table(["Rule", "Column", "Explanation / suggested action"], [
            [finding.rule, finding.column if finding.column is not None else "(whole dataset)", finding.message]
            for finding in inspection.findings
        ])
    else:
        lines += ["No potential issues detected by the configured rules. This does not guarantee clean data.", ""]

    lines += ["## Columns", ""]
    lines += _table(["Column", "Inferred type", "Missing", "Missing %", "Distinct (non-missing)", "Observed types"], [
        [column.name, column.inferred_type, f"{column.missing_count:,}", f"{column.missing_fraction:.1%}",
         f"{column.distinct_count:,}",
         ", ".join(f"{kind}: {count:,}" for kind, count in sorted(column.type_counts.items())) or "none"]
        for column in inspection.columns
    ])

    lines += [
        "## Numeric summaries", "",
        ("Only numeric cells are included; missing values, text and booleans are excluded. "
         "For mixed columns, statistics describe the numeric subset only. Values are shown to six significant digits."), "",
    ]
    numeric_rows = [
        [column.name, f"{column.numeric.count:,}", _number(column.numeric.minimum),
         _number(column.numeric.maximum), _number(column.numeric.mean)]
        for column in inspection.columns if column.numeric is not None
    ]
    if numeric_rows:
        lines += _table(["Column", "Numeric values", "Minimum", "Maximum", "Mean"], numeric_rows)
    else:
        lines += ["No numeric values to summarize.", ""]

    lines += [
        "## Categorical summaries", "",
        (f"String, boolean and mixed columns; up to {config.top_values} most frequent non-missing values. "
         "Counts use original values, with ties in first-seen order. Strings are quoted to distinguish them from numbers."), "",
    ]
    categorical_rows = [
        [column.name, f"{column.distinct_count:,}",
         "; ".join(f"{_value(value)} ({count:,})" for value, count in column.top_values)]
        for column in inspection.columns
        if column.inferred_type in {"string", "boolean", "mixed"}
    ]
    if categorical_rows:
        lines += _table(["Column", "Unique values", "Most frequent values (count)"], categorical_rows)
    else:
        lines += ["No categorical values to summarize.", ""]

    markers = ", ".join(_value(value) for value in sorted(set(config.missing_values) | {""}))
    lines += [
        "## Rules and limitations", "",
        ("- Missingness: JSON null, absent keys and blank/whitespace-only strings are always missing. "
         f"Configured text markers (case-insensitive, trimmed): {_escape(markers)}."),
        f"- High missingness: missing fraction >= {config.missing_threshold:.1%}, including fully missing columns.",
        ("- Duplicates: repeated full rows beyond their first occurrence, after missing-value normalization. "
         "Original CSV strings are otherwise unchanged; JSON 1 and 1.0 compare equal, but true and 1 do not."),
        ("- Types: CSV recognizes signed integers, decimal/scientific numbers and true/false (case-insensitive). "
         "JSON preserves native types, so quoted numbers remain strings. Integer and number are compatible; "
         "other combinations trigger the mixed-type rule. Entirely missing columns are typed empty."),
        ("- Mixed types can be intentional in identifiers or categorical codes (for example, point groups). "
         "No domain schema or expected units are assumed; dates remain strings."),
        ("- Summary statistics include duplicate rows. Missing values are excluded from distinct counts and frequency tables. "
         "No rows are repaired, removed or imputed, and the source file is never modified."),
        ("- Scope: UTF-8 comma-separated CSV with a header, or a JSON array of flat objects. "
         "The full dataset is loaded into memory. No nested JSON, JSON Lines, outlier detection or domain validation."),
        "",
    ]
    return "\n".join(lines)
