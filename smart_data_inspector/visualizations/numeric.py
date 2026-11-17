"""Distribution chart generators for selected numerical measurements."""

from pathlib import Path

import numpy as np
import pandas as pd

from .common import figure


def _finite(frame: pd.DataFrame, name: str) -> pd.Series:
    return pd.to_numeric(frame[name], errors="coerce").astype("float64").replace([np.inf, -np.inf], np.nan).dropna()


def plot_numeric_distributions(frame: pd.DataFrame, columns: list[str], output_dir: Path) -> Path | None:
    """Save histograms for up to six selected finite numeric columns."""
    pairs = [(name, series) for name in columns[:6] if not (series := _finite(frame, name)).empty]
    if not pairs:
        return None
    path = output_dir / "numeric_distributions.png"
    with figure(len(pairs), 1, figsize=(7, 2.7 * len(pairs)), squeeze=False) as (fig, axes):
        for axis, (name, series) in zip(axes[:, 0], pairs):
            axis.hist(series, bins=min(30, max(5, int(np.sqrt(len(series))))), color="#4477aa", edgecolor="white")
            axis.set(title=str(name), ylabel="Records")
        axes[-1, 0].set_xlabel("Value")
        fig.suptitle("Selected numerical distributions", y=1.01)
        fig.tight_layout()
        fig.savefig(path, dpi=160, bbox_inches="tight")
    return path


def plot_numeric_boxplots(frame: pd.DataFrame, columns: list[str], output_dir: Path) -> Path | None:
    """Save comparative boxplots where at least one selected column has values."""
    pairs = [(name, values) for name in columns[:6] if len(values := _finite(frame, name)) >= 2]
    if not pairs:
        return None
    path = output_dir / "numeric_boxplots.png"
    with figure(figsize=(max(6, 1.1 * len(pairs)), 4)) as (fig, axis):
        axis.boxplot([values for _, values in pairs], tick_labels=[str(name) for name, _ in pairs], showfliers=True)
        axis.set(title="Selected numerical ranges and potential extremes", ylabel="Value")
        axis.tick_params(axis="x", rotation=35, labelsize=9)
        fig.tight_layout()
        fig.savefig(path, dpi=160)
    return path
