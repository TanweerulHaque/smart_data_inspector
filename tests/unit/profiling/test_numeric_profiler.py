"""Finite float summaries, sample statistics and overflow-resistant arithmetic."""

import math

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from smart_data_inspector.profiling.numeric.profiler import profile_numeric


@pytest.mark.parametrize("values", [[], [None, np.nan, pd.NA]])
def test_empty_or_all_null_has_no_defined_statistics(values):
    summary = profile_numeric(pd.Series(values, dtype=object))
    assert summary.count == 0
    assert summary.nonfinite_count == 0
    assert (summary.minimum, summary.maximum, summary.mean, summary.median,
            summary.std, summary.q1, summary.q3) == (None,) * 7


def test_single_finite_value_has_quartiles_but_no_sample_std():
    summary = profile_numeric(pd.Series([None, 7.5, np.nan]))
    assert summary.count == 1
    assert (summary.minimum, summary.maximum, summary.mean, summary.median,
            summary.q1, summary.q3) == (7.5,) * 6
    assert summary.std is None


def test_normal_statistics_use_sample_std_and_linear_quartiles_without_mutation():
    series = pd.Series([1, 2, None, 3, 4], dtype=object, name="measurement")
    before = series.copy(deep=True)
    summary = profile_numeric(series)
    assert summary.count == 4
    assert summary.nonfinite_count == 0
    assert (summary.minimum, summary.maximum) == (1, 4)
    assert summary.mean == pytest.approx(2.5)
    assert summary.median == pytest.approx(2.5)
    assert summary.std == pytest.approx(math.sqrt(5 / 3))
    assert (summary.q1, summary.q3) == pytest.approx((1.75, 3.25))
    assert_series_equal(series, before)


def test_fractional_mean_is_accurate_with_float_tolerance():
    summary = profile_numeric(pd.Series([0.1, 0.2, 0.3]))
    assert (summary.minimum, summary.maximum, summary.mean) == pytest.approx((0.1, 0.3, 0.2))


def test_repeated_extreme_values_do_not_overflow_the_mean():
    summary = profile_numeric(pd.Series([1e308, 1e308, 1e308, 1e308]))
    assert summary.count == 4
    assert (summary.minimum, summary.maximum, summary.mean, summary.median,
            summary.q1, summary.q3) == pytest.approx((1e308,) * 6)
    assert summary.std == 0
    assert summary.mean is not None
    assert math.isfinite(summary.mean)


def test_extreme_signed_values_have_finite_interpolated_quartiles():
    summary = profile_numeric(pd.Series([-1e308, -5e307, 5e307, 1e308]))
    assert summary.mean == pytest.approx(0)
    assert summary.median == pytest.approx(0)
    assert (summary.q1, summary.q3) == pytest.approx((-6.25e307, 6.25e307))
    assert summary.std == pytest.approx(math.sqrt(5 / 6) * 1e308)
    for value in (summary.q1, summary.q3, summary.std):
        assert value is not None
        assert math.isfinite(value)


def test_cancellation_keeps_small_contributions_to_mean():
    summary = profile_numeric(pd.Series([1e30, 1, -1e30]))
    assert summary.mean == pytest.approx(1 / 3)


def test_unrepresentable_sample_std_is_unavailable_not_infinite():
    summary = profile_numeric(pd.Series([-1.7e308, 1.7e308]))
    assert summary.count == 2
    assert summary.mean == pytest.approx(0)
    assert summary.std is None
    assert (summary.q1, summary.q3) == pytest.approx((-8.5e307, 8.5e307))


def test_infinities_are_counted_separately_and_excluded_from_statistics():
    summary = profile_numeric(pd.Series([None, np.nan, -np.inf, 1, 3, np.inf]))
    assert (summary.count, summary.nonfinite_count) == (2, 2)
    assert (summary.minimum, summary.maximum, summary.mean, summary.median) == (1, 3, 2, 2)
    assert summary.std == pytest.approx(math.sqrt(2))


def test_only_infinities_have_no_finite_summary():
    summary = profile_numeric(pd.Series([-np.inf, np.inf]))
    assert (summary.count, summary.nonfinite_count) == (0, 2)
    assert (summary.minimum, summary.maximum, summary.mean, summary.median,
            summary.std, summary.q1, summary.q3) == (None,) * 7
