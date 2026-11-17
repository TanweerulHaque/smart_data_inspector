"""Date/time quality prompts: future values, impossible calendar dates, mixed formats."""

from ..models import ColumnSummary, Finding


def check_dates(column: ColumnSummary) -> list[Finding]:
    summary = column.datetime
    if summary is None:
        return []
    findings: list[Finding] = []
    if summary.invalid_count:
        findings.append(Finding(
            "Invalid calendar dates", column.name, "warning",
            f"{summary.invalid_count:,} ISO-shaped value(s) are not real dates/times; examples: {summary.invalid_examples!r}.",
            "Matches the ISO date pattern but fails calendar parsing (e.g. month 13, 30 February).",
            "Check data entry or export; these values cannot be ordered or compared.",
        ))
    if summary.future_count:
        findings.append(Finding(
            "Future dates", column.name, "warning",
            f"{summary.future_count:,}/{summary.count:,} parsed value(s) are later than the inspection time "
            f"{summary.reference_time}; examples: {summary.future_examples!r}.",
            "Value > inspection time (UTC; naive values treated as UTC; date-only values compared by day).",
            "Future values are valid for schedules or forecasts, but often indicate typos or wrong year/format.",
        ))
    if len(summary.formats) > 1 or (summary.timezone_aware_count and summary.naive_count):
        listed = ", ".join(f"{label}: {count:,}" for label, count in sorted(summary.formats.items()))
        zone = (f" Timezone-aware: {summary.timezone_aware_count:,}, naive: {summary.naive_count:,}."
                if summary.timezone_aware_count and summary.naive_count else "")
        examples = f" Non-ISO examples: {summary.non_iso_examples!r}." if summary.non_iso_examples else ""
        findings.append(Finding(
            "Mixed date formats", column.name, "warning" if summary.non_iso_count else "info",
            f"Observed {listed}.{zone}{examples}",
            "More than one date/time layout (or timezone-aware and naive values) in one column.",
            "Mixed layouts are easy to mis-parse (e.g. 03/04/2024 is day-first or month-first); standardise before analysis.",
        ))
    return findings
