"""Explain missing coverage, including below-threshold missingness."""

from ...config import InspectionConfig
from ...models import Finding, MissingSummary


def check_missingness(column: str, summary: MissingSummary, config: InspectionConfig) -> list[Finding]:
    if not summary.missing_count:
        return []
    high = summary.missing_fraction >= config.missing_threshold
    return [Finding(
        "High missingness" if high else "Missing values", column, "warning" if high else "info",
        f"{summary.missing_count:,} missing of {summary.missing_count + summary.non_null_count:,} "
        f"values ({summary.missing_fraction:.2%}).",
        f"High missingness when missing fraction >= {config.missing_threshold:.1%}; any missing values are reported.",
        "Review collection coverage before relying on this column; no imputation has been performed.",
    )]
