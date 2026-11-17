"""Missing-value normalization and counts, independently usable on DataFrames."""

import pandas as pd

from ...config import DEFAULT_MISSING_VALUES
from ...models import MissingSummary


def normalize_missing(frame: pd.DataFrame, markers: tuple[str, ...] = DEFAULT_MISSING_VALUES) -> pd.DataFrame:
    """Return a new frame; preserve nonmissing values, including 0 and False."""
    tokens = {value.strip().casefold() for value in markers} | {""}
    result = frame.copy(deep=True)
    for name in frame.columns:
        series = frame[name]
        text_missing = series.map(lambda value: isinstance(value, str) and value.strip().casefold() in tokens)
        result[name] = series.mask(series.isna() | text_missing, None).astype(object)
    return result


def profile_missingness(series: pd.Series) -> MissingSummary:
    """Count nulls safely even for an empty Series."""
    missing = int(series.isna().sum())
    return MissingSummary(missing, missing / len(series) if len(series) else 0.0, len(series) - missing)
