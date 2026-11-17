"""Numerical correlation heatmap generator."""

from pathlib import Path

import numpy as np
import pandas as pd

from .common import figure


def plot_correlation_heatmap(frame: pd.DataFrame, columns: list[str], output_dir: Path) -> Path | None:
    """Save a Pearson heatmap when two or more numeric variables are available."""
    selected = columns[:12]
    if len(selected) < 2:
        return None
    numeric = frame[selected].apply(pd.to_numeric, errors="coerce").astype("float64").replace([np.inf, -np.inf], np.nan)
    correlation = numeric.corr(method="pearson", min_periods=3)
    if correlation.dropna(how="all").empty:
        return None
    path = output_dir / "correlation_heatmap.png"
    with figure(figsize=(max(5, 0.7 * len(selected)), max(4, 0.6 * len(selected)))) as (fig, axis):
        image = axis.imshow(correlation, vmin=-1, vmax=1, cmap="coolwarm")
        fig.suptitle("Pearson correlation among numerical variables", fontsize=12)
        axis.set_xticks(range(len(selected)), [str(name) for name in selected], rotation=40, ha="right", fontsize=8)
        axis.set_yticks(range(len(selected)), [str(name) for name in selected], fontsize=8)
        fig.colorbar(image, ax=axis, label="Correlation")
        fig.tight_layout(rect=(0, 0, 1, 0.95))
        fig.savefig(path, dpi=160)
    return path
