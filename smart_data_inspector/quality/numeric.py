"""Explainable distribution checks; observations are never treated as errors."""

from ..config import InspectionConfig
from ..models import ColumnSummary, Finding


def check_numeric_quality(column: ColumnSummary, config: InspectionConfig) -> list[Finding]:
    """Flag constant/near-constant and zero-heavy numerical variables."""
    numeric = column.numeric
    if numeric is None or numeric.count == 0 or column.likely_identifier:
        return []
    findings: list[Finding] = []
    if numeric.minimum == numeric.maximum:
        findings.append(Finding("Constant numeric column", column.name, "warning", "All finite numeric values are identical.",
                                "Minimum equals maximum among finite numeric values.",
                                "A constant measurement cannot explain variation; check whether this is expected."))
    elif numeric.mode is not None:
        # Compute dominant frequency from categorical profiling, which retains native values.
        dominant = column.top_values[0][1] if column.top_values else 0
        if dominant / numeric.count >= config.near_constant_threshold:
            findings.append(Finding("Near-constant numeric column", column.name, "info",
                                    f"Most frequent observed value accounts for {dominant / numeric.count:.1%} of finite values.",
                                    f"Dominant-value fraction >= {config.near_constant_threshold:.0%}.",
                                    "This may add little variation, but can be a valid censored or rounded measurement."))
    if numeric.zero_fraction >= config.excessive_zero_threshold:
        findings.append(Finding("Excessive zeros", column.name, "info",
                                f"{numeric.zero_count:,}/{numeric.count:,} finite values ({numeric.zero_fraction:.1%}) are zero.",
                                f"Zero fraction >= {config.excessive_zero_threshold:.0%}.",
                                "Determine whether zero is a true measurement, a sentinel, or a structural absence."))
    return findings
