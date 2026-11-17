"""Small shared safeguards around Pandas float64 processing."""

import math
from typing import Any

import numpy as np
import pandas as pd


def as_numeric_series(series: pd.Series) -> pd.Series:
    """Convert numeric scalars/tokens consistently, retaining overflow as signed infinity."""
    def convert(value: Any) -> float:
        try:
            return float(value)
        except OverflowError:
            return -math.inf if value < 0 else math.inf
        except (TypeError, ValueError):
            return math.nan

    return series.map(convert).astype("float64")


def numeric_quantiles(finite: pd.Series) -> pd.Series:
    """Use unscaled Pandas quartiles; repair overflow in interpolation only when needed."""
    with np.errstate(over="ignore", invalid="ignore"):
        result = finite.quantile([0.25, 0.5, 0.75])
    if np.isfinite(result).all():
        return result
    ordered = finite.sort_values().reset_index(drop=True)
    for probability in result.index:
        if not math.isfinite(result.loc[probability]):
            position = (len(ordered) - 1) * probability
            lower = math.floor(position)
            weight = position - lower
            left, right = float(ordered.iloc[lower]), float(ordered.iloc[math.ceil(position)])
            result.loc[probability] = math.fsum((left * (1 - weight), right * weight))
    return result
