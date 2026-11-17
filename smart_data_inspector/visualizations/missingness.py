"""Charts for column and row missingness."""

from pathlib import Path

import pandas as pd

from .common import figure


def plot_missingness(frame: pd.DataFrame, output_dir: Path) -> Path | None:
    """Save a ranked column-missingness bar chart when missing values exist."""
    counts = frame.isna().sum().sort_values(ascending=False)
    counts = counts[counts > 0]
    if counts.empty:
        return None
    path = output_dir / "missingness.png"
    with figure(figsize=(max(6, len(counts) * 0.75), 4)) as (fig, axis):
        axis.bar(counts.index.astype(str), counts.values, color="#3d6b99")
        axis.set(title="Missing values by column", ylabel="Missing records")
        axis.tick_params(axis="x", rotation=35, labelsize=9)
        fig.tight_layout()
        fig.savefig(path, dpi=160)
    return path


def plot_row_missingness(frame: pd.DataFrame, output_dir: Path) -> Path | None:
    """Save row-wise missing cell distribution for a non-empty table."""
    if frame.empty or not frame.isna().to_numpy().any():
        return None
    path = output_dir / "row_missingness.png"
    counts = frame.isna().sum(axis=1)
    with figure(figsize=(6, 4)) as (fig, axis):
        axis.hist(counts, bins=range(0, int(counts.max()) + 2), align="left", color="#6a9f58", rwidth=0.8)
        axis.set(title="Missing cells per record", xlabel="Missing cells", ylabel="Number of records")
        fig.tight_layout()
        fig.savefig(path, dpi=160)
    return path
