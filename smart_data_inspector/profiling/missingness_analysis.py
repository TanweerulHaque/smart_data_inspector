"""Dataset-level missingness patterns, separate from column-level counts."""

from collections import Counter

import pandas as pd

from ..config import InspectionConfig
from ..models import MissingPattern, MissingnessProfile


def profile_missingness_patterns(frame: pd.DataFrame,
                                 config: InspectionConfig | None = None) -> MissingnessProfile:
    """Count row burden, repeated missing-column sets, and pair co-occurrence."""
    config = config or InspectionConfig()
    if frame.empty:
        return MissingnessProfile(0, 0, [], 0, [], [])
    mask = frame.isna().to_numpy()
    names = [str(column) for column in frame.columns]
    row_counts = mask.sum(axis=1).astype(int).tolist()
    patterns = Counter(map(tuple, mask[mask.any(axis=1)]))
    relevant = [MissingPattern(tuple(name for name, missing in zip(names, pattern) if missing), count)
                for pattern, count in patterns.most_common(config.top_values)]
    together = mask.T.astype(int) @ mask.astype(int)  # records missing both columns
    pairs = [(names[left], names[right], int(together[left, right]))
             for left in range(len(names)) for right in range(left + 1, len(names)) if together[left, right]]
    cooccurrences = sorted(pairs, key=lambda pair: -pair[2])[:config.top_values]
    return MissingnessProfile(
        total_missing=int(mask.sum()), total_cells=frame.shape[0] * frame.shape[1],
        row_missing_counts=row_counts,
        high_missing_rows=sum(count / frame.shape[1] >= config.row_missing_threshold for count in row_counts),
        patterns=relevant, cooccurrences=cooccurrences,
    )
