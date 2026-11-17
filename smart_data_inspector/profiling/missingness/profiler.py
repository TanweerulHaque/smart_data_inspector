"""Missing-value normalization and counts."""

import pandas as pd
from pandas.api.types import is_object_dtype, is_string_dtype

from ...config import DEFAULT_MISSING_VALUES
from ...models import MissingSummary


def normalize_missing(frame: pd.DataFrame, markers: tuple[str, ...] = DEFAULT_MISSING_VALUES) -> dict[str, dict[str, int]]:
    """Replace marker text with missing values in place; return converted counts per column.

    Trimmed text must equal a marker exactly (case-sensitive); blank text is always missing.
    """
    tokens = {value.strip() for value in markers} | {""}
    conversions: dict[str, dict[str, int]] = {}
    for name in frame.columns:
        series = frame[name]
        if not (is_object_dtype(series) or is_string_dtype(series)):
            continue
        stripped = series.map(lambda value: value.strip() if isinstance(value, str) else None)
        hits = stripped.isin(tokens)
        if hits.any():
            conversions[str(name)] = {str(token): int(count) for token, count in stripped[hits].value_counts().items()}
            frame.loc[hits, name] = None
    return conversions


def profile_missingness(series: pd.Series) -> MissingSummary:
    """Count nulls safely even for an empty Series."""
    missing = int(series.isna().sum())
    return MissingSummary(missing, missing / len(series) if len(series) else 0.0, len(series) - missing)
