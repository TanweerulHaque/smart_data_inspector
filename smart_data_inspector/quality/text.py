"""Formatting and rare-value checks for string-like categorical data."""

from ..config import InspectionConfig
from ..models import ColumnSummary, Finding


def check_text_quality(column: ColumnSummary, config: InspectionConfig) -> list[Finding]:
    """Return evidence-backed prompts for values that could split categories."""
    if column.likely_identifier or column.inferred_type not in {"string", "mixed", "boolean"}:
        return []
    findings: list[Finding] = []
    text = column.text
    if text and text.whitespace_count:
        findings.append(Finding("Whitespace inconsistencies", column.name, "info",
                                f"{text.whitespace_count:,}/{text.count:,} string value(s) have leading or trailing whitespace.",
                                "String value differs from its stripped form.",
                                "Inspect whether trimming would merge labels; the tool does not alter values."))
    if text and text.casefold_collision_count:
        findings.append(Finding("Case inconsistencies", column.name, "info",
                                f"At least {text.casefold_collision_count:,} distinct string label(s) collapse under case-insensitive comparison.",
                                "Distinct observed strings share a Unicode case-folded form.",
                                "Review capitalization before grouping categories."))
    if column.non_null_count and column.distinct_count <= 50 and column.rare_count:
        examples = ", ".join(repr(value) for value in column.rare_examples)
        if examples:
            findings.append(Finding("Rare categories", column.name, "info",
                                    f"{column.rare_count:,} category value(s) occur in at most {config.rare_category_threshold:.1%} of non-missing records; examples: {examples}.",
                                    f"Category frequency <= {config.rare_category_threshold:.1%}; evaluated for columns with at most 50 distinct values.",
                                    "Rare labels may be valid minority classes, spelling variants, or data-entry errors."))
    return findings
