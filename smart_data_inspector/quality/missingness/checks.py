"""Explain missing coverage, including below-threshold missingness and marker conversions."""

import re

import pandas as pd

from ...config import InspectionConfig
from ...models import Finding, MissingSummary

SHORT_CODE = re.compile(r"[A-Za-z]{1,3}\Z")


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


def _looks_like_short_codes(present: pd.Series) -> list[str]:
    """Return examples when most remaining values are short alphabetic codes (e.g. K, Cl, US)."""
    strings = [value.strip() for value in present.tolist() if isinstance(value, str)]
    if not strings or len(strings) < 0.8 * len(present):
        return []
    distinct = list(dict.fromkeys(strings))
    codes = [value for value in distinct if SHORT_CODE.fullmatch(value)]
    return codes[:5] if len(codes) >= 0.8 * len(distinct) else []


def check_marker_conversions(column: str, conversions: dict[str, int], present: pd.Series) -> list[Finding]:
    """Make text-marker conversions visible; warn when a marker may be a real code like 'NA'."""
    tokens = {token: count for token, count in conversions.items() if token}
    if not tokens:
        return []
    listed = ", ".join(f"{token!r} ×{count:,}" for token, count in sorted(tokens.items()))
    rule = "Trimmed text exactly equal (case-sensitive) to a configured missing-value marker is treated as missing."
    codes = _looks_like_short_codes(present)
    ambiguous = [token for token in tokens if SHORT_CODE.fullmatch(token)]
    if codes and ambiguous:
        return [Finding(
            "Ambiguous missing-value marker", column, "warning",
            f"Converted to missing: {listed}; the other values are short codes such as {codes!r}.",
            rule + " Flagged when the column's remaining values are mostly 1-3 letter codes.",
            f"{', '.join(repr(token) for token in ambiguous)} may be a legitimate code (e.g. 'NA' for sodium, "
            "Namibia or North America). Re-run with --missing-value/--no-missing-markers if so.",
        )]
    return [Finding(
        "Missing-value markers converted", column, "info", f"Converted to missing: {listed}.", rule,
        "Confirm these tokens mean 'unknown' in this dataset; change them with --missing-value or --no-missing-markers.",
    )]
