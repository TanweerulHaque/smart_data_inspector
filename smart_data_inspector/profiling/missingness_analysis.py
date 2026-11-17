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
    mask = frame.isna()
    row_counts = mask.sum(axis=1).astype(int).tolist()
    patterns = Counter(tuple(str(column) for column in frame.columns[mask.iloc[index].to_numpy()])
                       for index in range(len(frame)))
    relevant = [MissingPattern(columns, count) for columns, count in patterns.most_common(config.top_values)
                if columns]
    pairs: Counter[tuple[str, str]] = Counter()
    for _, row in mask.iterrows():
        names = [str(column) for column, missing in row.items() if missing]
        for index, left in enumerate(names):
            for right in names[index + 1:]:
                pairs[(left, right)] += 1
    cooccurrences = [(left, right, count) for (left, right), count in pairs.most_common(config.top_values)]
    return MissingnessProfile(
        total_missing=int(mask.to_numpy().sum()), total_cells=frame.shape[0] * frame.shape[1],
        row_missing_counts=row_counts,
        high_missing_rows=sum(count / frame.shape[1] >= config.row_missing_threshold for count in row_counts),
        patterns=relevant, cooccurrences=cooccurrences,
    )
