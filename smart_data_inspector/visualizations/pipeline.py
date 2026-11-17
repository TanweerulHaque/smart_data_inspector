"""Explicit chart orchestration. Individual failures never stop inspection, and
every chart's outcome (generated / not applicable / failed) is recorded for the report."""

from collections.abc import Callable
from pathlib import Path

import pandas as pd

from ..models import ChartAsset, ChartStatus, Inspection
from .categorical import plot_category_frequencies
from .missingness import plot_missingness, plot_row_missingness
from .numeric import plot_numeric_boxplots, plot_numeric_distributions
from .relationships import plot_correlation_heatmap


def generate_charts(frame: pd.DataFrame, inspection: Inspection, output_dir: Path,
                    link_prefix: str) -> tuple[list[ChartAsset], list[ChartStatus]]:
    """Write applicable PNGs into ``output_dir``.

    ``link_prefix`` is the report-relative directory the PNGs will finally live in;
    the caller may stage charts elsewhere and move them into place afterwards.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    assets: list[ChartAsset] = []
    statuses: list[ChartStatus] = []

    def add(key: str, title: str, caption: str, reason: str, factory: Callable[[], Path | None]) -> None:
        try:
            path = factory()
        except Exception as exc:  # noqa: BLE001 - one chart must never abort a report
            statuses.append(ChartStatus(key, title, "failed", f"{type(exc).__name__}: {exc}"))
            return
        if path is None:
            statuses.append(ChartStatus(key, title, "not applicable", reason))
            return
        assets.append(ChartAsset(key, f"{link_prefix}/{path.name}", caption))
        statuses.append(ChartStatus(key, title, "generated", path.name))

    add("missingness", "Missing values by column", "Columns ranked by the number of missing records.",
        "no missing values", lambda: plot_missingness(frame, output_dir))
    add("row_missingness", "Missing cells per record", "Distribution of missing-cell burden across records.",
        "no missing values", lambda: plot_row_missingness(frame, output_dir))
    numeric = [column.name for column in inspection.columns if column.numeric is not None and not column.likely_identifier]
    add("numeric_distributions", "Numerical histograms",
        "Histograms for selected numerical measurements; interpret scales separately.",
        "no non-identifier numeric column with finite values",
        lambda: plot_numeric_distributions(frame, numeric, output_dir))
    add("numeric_boxplots", "Numerical boxplots",
        "Selected numerical ranges; points beyond whiskers are distributional candidates, not errors.",
        "no numeric column with at least 2 finite values",
        lambda: plot_numeric_boxplots(frame, numeric, output_dir))
    add("correlations", "Correlation heatmap",
        "Pearson correlations among selected numerical variables; association is not causation.",
        "fewer than 2 numeric columns with enough complete pairs",
        lambda: plot_correlation_heatmap(frame, numeric, output_dir))
    candidates = [column.name for column in inspection.columns
                  if not column.likely_identifier and 2 <= column.distinct_count <= 10
                  and column.inferred_type in {"string", "boolean", "mixed"}]
    name = candidates[0] if candidates else None
    add("categories", f"Category frequencies{f' ({name})' if name else ''}",
        f"Most frequent observed values for {name}.",
        "no non-identifier categorical column with 2-10 distinct values",
        (lambda: plot_category_frequencies(frame, name, output_dir, inspection.config.top_values))
        if name is not None else (lambda: None))
    return assets, statuses
