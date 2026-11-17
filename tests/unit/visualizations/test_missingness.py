import pandas as pd

from smart_data_inspector.visualizations.missingness import plot_missingness


def test_missingness_chart_is_a_closed_png_or_skipped(tmp_path):
    chart = plot_missingness(pd.DataFrame({"a": [1, None, 3]}), tmp_path)
    assert chart is not None
    assert chart.exists() and chart.stat().st_size > 0
    assert plot_missingness(pd.DataFrame({"a": [1, 2]}), tmp_path) is None
