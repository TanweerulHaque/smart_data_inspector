"""Distribution-based potential outliers, without domain-specific acceptable ranges."""

from typing import cast

import numpy as np
import pandas as pd

from ...config import InspectionConfig
from ...models import Finding
from ...utils.numeric import as_numeric_series, numeric_quantiles


def check_outliers(column: str, series: pd.Series, config: InspectionConfig) -> list[Finding]:
    """Apply strict IQR fences to finite values; skip small samples and zero IQR."""
    values = as_numeric_series(series).dropna()
    values = cast(pd.Series, values[np.isfinite(values)])
    if len(values) < config.outlier_min_count:
        return []
    quartiles = numeric_quantiles(values)
    q1, q3 = float(quartiles.loc[0.25]), float(quartiles.loc[0.75])
    iqr = q3 - q1
    if iqr <= 0:
        return []
    lower, upper = q1 - config.iqr_multiplier * iqr, q3 + config.iqr_multiplier * iqr
    outliers = cast(pd.Series, values[(values < lower) | (values > upper)])
    if outliers.empty:
        return []
    examples = ", ".join(f"{value:.6g}" for value in outliers.drop_duplicates().iloc[:config.top_values])
    return [Finding(
        "Potential numerical outliers", column, "info",
        f"{len(outliers):,}/{len(values):,} finite numeric values outside IQR fences "
        f"[{lower:.6g}, {upper:.6g}]. Examples: {examples}.",
        f"x < Q1 - {config.iqr_multiplier:g} × IQR or x > Q3 + {config.iqr_multiplier:g} × IQR; "
        "linear quartiles, strict inequalities.",
        "Potential outliers are not confirmed errors. Skewed or multimodal distributions may naturally produce them.",
    )]
