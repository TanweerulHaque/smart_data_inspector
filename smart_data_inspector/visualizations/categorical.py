"""Frequency charts for low-cardinality non-identifier columns."""

from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def plot_category_frequencies(frame: pd.DataFrame, column: str, output_dir: Path, limit: int = 10) -> Path | None:
    """Save one ranked category chart; unsuitable high-cardinality input is skipped."""
    counts = frame[column].dropna().value_counts().head(limit)
    if counts.empty or counts.index.nunique() > limit:
        return None
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", str(column)).strip("._") or "column"
    path = output_dir / f"categories_{safe_name}.png"
    figure, axis = plt.subplots(figsize=(7, max(3, len(counts) * 0.42)))
    axis.barh([str(value) for value in counts.index[::-1]], counts.values[::-1], color="#aa6655")
    axis.set(title=f"Most frequent values: {column}", xlabel="Records")
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path
