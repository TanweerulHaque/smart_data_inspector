"""Frequency charts for low-cardinality non-identifier columns."""

from pathlib import Path

import pandas as pd

from .common import figure, safe_chart_path


def plot_category_frequencies(frame: pd.DataFrame, column: str, output_dir: Path, limit: int = 10) -> Path | None:
    """Save one ranked category chart; unsuitable high-cardinality input is skipped."""
    counts = frame[column].dropna().map(str).value_counts().head(limit)
    if counts.empty:
        return None
    path = safe_chart_path(output_dir, "categories", column)
    with figure(figsize=(7, max(3, len(counts) * 0.42))) as (fig, axis):
        axis.barh(list(counts.index[::-1]), counts.values[::-1], color="#aa6655")
        axis.set(title=f"Most frequent values: {column}", xlabel="Records")
        fig.tight_layout()
        fig.savefig(path, dpi=160)
    return path
