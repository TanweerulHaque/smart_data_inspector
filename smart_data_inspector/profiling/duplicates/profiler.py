"""Exact full-row duplicate counting after explicit missing normalization."""

import pandas as pd

from ...utils.serialization import value_keys


def profile_duplicates(frame: pd.DataFrame) -> int:
    """Count additional occurrences, not every member of a duplicate group."""
    if frame.empty:
        return 0
    signatures = frame.apply(value_keys)
    return int(signatures.duplicated(keep="first").sum())
