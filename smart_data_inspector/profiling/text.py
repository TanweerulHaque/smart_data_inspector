"""Small, explainable text-profile summaries; input is never modified."""

import pandas as pd

from ..models import TextSummary


def profile_text(series: pd.Series) -> TextSummary | None:
    """Summarise actual string values without treating missing values as text."""
    values = [value for value in series.dropna().tolist() if isinstance(value, str)]
    if not values:
        return None
    lengths = [len(value) for value in values]
    normalized = {value.casefold() for value in values}
    return TextSummary(
        count=len(values),
        empty_count=sum(not value for value in values),
        whitespace_count=sum(value != value.strip() for value in values),
        casefold_collision_count=len(set(values)) - len(normalized),
        minimum_length=min(lengths), maximum_length=max(lengths),
        mean_length=sum(lengths) / len(lengths),
    )
