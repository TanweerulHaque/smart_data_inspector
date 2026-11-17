"""Exact full-row duplicate counting after explicit missing normalization."""

import pandas as pd

from ...utils.serialization import value_key


def profile_duplicates(frame: pd.DataFrame) -> int:
    """Count additional occurrences, not every member of a duplicate group."""
    if frame.empty:
        return 0
    signatures = frame.apply(lambda column: column.map(value_key))
    return int(signatures.duplicated(keep="first").sum())
