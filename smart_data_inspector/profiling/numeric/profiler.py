"""Finite-value numeric summaries with overflow-resistant scaling."""

import math
from decimal import Decimal
from statistics import mean
from typing import cast

import numpy as np
import pandas as pd

from ...models import NumericSummary
from ...utils.numeric import as_numeric_series, numeric_quantiles


def profile_numeric(series: pd.Series) -> NumericSummary:
    """Summarize finite numbers; sample std uses ddof=1; no values => None statistics."""
    values = as_numeric_series(series).dropna()
    finite = cast(pd.Series, values[np.isfinite(values)])
    nonfinite = len(values) - len(finite)
    if finite.empty:
        return NumericSummary(0, None, None, None, None, None, None, None, nonfinite)
    scale = float(finite.abs().max()) or 1.0
    normalized = finite / scale
    quartiles = numeric_quantiles(finite)
    # fsum preserves small contributions during cancellation; scaling handles overflowing sums.
    try:
        average = math.fsum(finite.tolist()) / len(finite)
    except OverflowError:
        average = float(mean(Decimal.from_float(value) for value in finite))
    with np.errstate(over="ignore", invalid="ignore"):
        std = float(normalized.std(ddof=1)) * scale if len(finite) > 1 else None
    if std is not None and not math.isfinite(std):
        std = None
    return NumericSummary(
        len(finite), float(finite.min()), float(finite.max()), average,
        float(quartiles.loc[0.5]), std,
        float(quartiles.loc[0.25]), float(quartiles.loc[0.75]), nonfinite,
    )
