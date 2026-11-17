"""Explicit chart orchestration. Individual failures never stop inspection."""

import os
from pathlib import Path

import pandas as pd

from ..models import ChartAsset, Inspection
from .categorical import plot_category_frequencies
from .missingness import plot_missingness, plot_row_missingness
from .numeric import plot_numeric_boxplots, plot_numeric_distributions
from .relationships import plot_correlation_heatmap


def generate_charts(frame: pd.DataFrame, inspection: Inspection, output_dir: Path,
                    report_dir: Path) -> list[ChartAsset]:
    """Generate applicable PNGs, returning report-relative paths and captions."""
    output_dir.mkdir(parents=True, exist_ok=False)
    assets: list[ChartAsset] = []

    def add(key: str, caption: str, factory) -> None:
        try:
            path = factory()
        except (ArithmeticError, OSError, ValueError, TypeError):
            return
        if path is not None:
            assets.append(ChartAsset(key, os.path.relpath(path, report_dir).replace(os.sep, "/"), caption))

    add("missingness", "Columns ranked by the number of missing records.", lambda: plot_missingness(frame, output_dir))
    add("row_missingness", "Distribution of missing-cell burden across records.", lambda: plot_row_missingness(frame, output_dir))
    numeric = [column.name for column in inspection.columns if column.numeric is not None and not column.likely_identifier]
    add("numeric_distributions", "Histograms for selected numerical measurements; interpret scales separately.",
        lambda: plot_numeric_distributions(frame, numeric, output_dir))
    add("numeric_boxplots", "Selected numerical ranges; points beyond whiskers are distributional candidates, not errors.",
        lambda: plot_numeric_boxplots(frame, numeric, output_dir))
    add("correlations", "Pearson correlations among selected numerical variables; association is not causation.",
        lambda: plot_correlation_heatmap(frame, numeric, output_dir))
    candidates = [column.name for column in inspection.columns
                  if not column.likely_identifier and 2 <= column.distinct_count <= 10
                  and column.inferred_type in {"string", "boolean", "mixed"}]
    if candidates:
        name = candidates[0]
        add("categories", f"Most frequent observed values for {name}.",
            lambda: plot_category_frequencies(frame, name, output_dir, inspection.config.top_values))
    return assets
