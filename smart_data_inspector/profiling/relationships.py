"""Pairwise numerical associations, intentionally limited to interpretable pairs."""

import numpy as np
import pandas as pd

from ..config import InspectionConfig
from ..models import Relationship, RelationshipProfile


def profile_relationships(frame: pd.DataFrame, numeric_columns: list[str],
                          config: InspectionConfig | None = None) -> RelationshipProfile:
    """Return finite Pearson/Spearman pairs. Correlations do not imply causation."""
    config = config or InspectionConfig()
    usable = numeric_columns[:]
    if len(usable) < 2:
        return RelationshipProfile([], usable)
    numeric = frame[usable].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    if len(numeric) > config.sample_rows:
        numeric = numeric.iloc[:config.sample_rows]
    pairs: list[Relationship] = []
    for position, left in enumerate(usable):
        for right in usable[position + 1:]:
            paired = numeric[[left, right]].dropna()
            if len(paired) < 3 or paired[left].nunique() < 2 or paired[right].nunique() < 2:
                continue
            pairs.append(Relationship(
                left, right,
                float(paired[left].corr(paired[right], method="pearson")),
                # Pandas delegates method="spearman" to SciPy in some releases.
                # Rank then use Pearson so this remains a NumPy/Pandas-only implementation.
                float(paired[left].rank(method="average").corr(paired[right].rank(method="average"), method="pearson")), len(paired),
            ))
    pairs.sort(key=lambda pair: max(abs(pair.pearson or 0), abs(pair.spearman or 0)), reverse=True)
    return RelationshipProfile(pairs, usable)
