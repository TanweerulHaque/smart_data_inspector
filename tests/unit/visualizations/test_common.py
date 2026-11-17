import matplotlib.pyplot as plt
import pytest

from smart_data_inspector.visualizations.common import figure, safe_chart_path


def test_similar_labels_get_distinct_files_and_existing_files_are_not_reused(tmp_path):
    first, second = safe_chart_path(tmp_path, "categories", "a/b"), safe_chart_path(tmp_path, "categories", "a_b")
    assert first != second
    first.write_bytes(b"png")
    assert safe_chart_path(tmp_path, "categories", "a/b") != first


def test_figure_is_closed_even_when_plotting_fails():
    before = len(plt.get_fignums())
    with pytest.raises(ValueError), figure():
        raise ValueError("bad data")
    assert len(plt.get_fignums()) == before
