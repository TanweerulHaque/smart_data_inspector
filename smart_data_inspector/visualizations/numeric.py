"""Distribution chart generators for selected numerical measurements."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_numeric_distributions(frame: pd.DataFrame, columns: list[str], output_dir: Path) -> Path | None:
    """Save histograms for up to six selected finite numeric columns."""
    selected = columns[:6]
    if not selected:
        return None
    values = [pd.to_numeric(frame[name], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
              for name in selected]
    pairs = [(name, series) for name, series in zip(selected, values) if not series.empty]
    if not pairs:
        return None
    path = output_dir / "numeric_distributions.png"
    figure, axes = plt.subplots(len(pairs), 1, figsize=(7, 2.7 * len(pairs)), squeeze=False)
    for axis, (name, series) in zip(axes[:, 0], pairs):
        axis.hist(series, bins=min(30, max(5, int(np.sqrt(len(series))))), color="#4477aa", edgecolor="white")
        axis.set(title=str(name), ylabel="Records")
    axes[-1, 0].set_xlabel("Value")
    figure.suptitle("Selected numerical distributions", y=1.01)
    figure.tight_layout()
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_numeric_boxplots(frame: pd.DataFrame, columns: list[str], output_dir: Path) -> Path | None:
    """Save comparative boxplots where at least one selected column has values."""
    pairs = [(name, pd.to_numeric(frame[name], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna())
             for name in columns[:6]]
    pairs = [(name, values) for name, values in pairs if len(values) >= 2]
    if not pairs:
        return None
    path = output_dir / "numeric_boxplots.png"
    figure, axis = plt.subplots(figsize=(max(6, 1.1 * len(pairs)), 4))
    axis.boxplot([values for _, values in pairs], tick_labels=[str(name) for name, _ in pairs], showfliers=True)
    axis.set(title="Selected numerical ranges and potential extremes", ylabel="Value")
    axis.tick_params(axis="x", rotation=35, labelsize=9)
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path
