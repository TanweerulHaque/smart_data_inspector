"""Type-aware frequencies and conservative identifier hints."""

import re

import pandas as pd

from ...config import InspectionConfig
from ...models import CategoricalSummary
from ...utils.serialization import value_key


def is_likely_identifier(series: pd.Series, config: InspectionConfig, *, text_values: bool = True) -> bool:
    """Name plus high uniqueness, or a sufficiently large entirely unique text column."""
    present = series.dropna()
    if present.empty:
        return False
    keys = present.map(value_key)
    unique = int(keys.nunique())
    ratio = unique / len(present)
    id_name = bool(re.search(r"(^|[_\W])(id|uuid|guid|identifier|key)($|[_\W])", str(series.name), re.IGNORECASE))
    named = id_name and ratio >= config.identifier_unique_ratio
    unique_text = (text_values and len(present) >= config.identifier_min_count and unique == len(present)
                   and present.map(lambda value: isinstance(value, str)).all())
    return bool(named or unique_text)


def profile_categorical(series: pd.Series, config: InspectionConfig | None = None) -> CategoricalSummary:
    """Non-null counts; frequency ties retain first appearance; bool differs from 1."""
    config = config or InspectionConfig()
    present = series.dropna()
    keys = present.map(value_key)
    counts = keys.value_counts(sort=False).sort_values(ascending=False, kind="stable")
    representatives = dict(zip(keys, present))
    top = [(representatives[key], int(count)) for key, count in counts.iloc[:config.top_values].items()]
    return CategoricalSummary(int(keys.nunique()), top, is_likely_identifier(series, config))
