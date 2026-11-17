"""Finite-only IQR checks, inclusive sample eligibility and strict fences."""

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from smart_data_inspector.config import InspectionConfig
from smart_data_inspector.quality.outliers.checks import check_outliers


@pytest.mark.parametrize("values", [[], [None, np.nan], [1], [1, 2, 100], [5] * 8,
                                         [0, 0, 0, 0, 100], [-np.inf, np.inf]])
def test_skips_insufficient_finite_samples_or_zero_iqr(values):
    assert check_outliers("v", pd.Series(values, dtype=object), InspectionConfig()) == []


def test_finds_both_tails_with_finite_denominator_and_does_not_mutate_series():
    series = pd.Series([-100, 0, 1, 2, 3, 4, 100, None, np.nan, np.inf, -np.inf], dtype=object)
    before = series.copy(deep=True)
    finding, = check_outliers("measurement", series, InspectionConfig())
    assert (finding.check_name, finding.column, finding.severity) == (
        "Potential numerical outliers", "measurement", "info",
    )
    assert "2/7 finite numeric values" in finding.evidence
    assert "[-4, 8]" in finding.evidence
    assert "Examples: -100, 100." in finding.evidence
    assert "x < Q1 - 1.5" in finding.rule
    assert "x > Q3 + 1.5" in finding.rule
    assert "not confirmed errors" in finding.explanation
    assert_series_equal(series, before)


@pytest.mark.parametrize("values", [[0, 0, 0, 1, 1, 2, 2, 5], [-3, 0, 0, 1, 1, 2, 2, 4]])
def test_values_exactly_on_upper_or_lower_fence_are_not_outliers(values):
    assert check_outliers("v", pd.Series(values), InspectionConfig()) == []


def test_multiplier_changes_fences_and_findings():
    series = pd.Series([1, 2, 3, 4, 10])
    finding, = check_outliers("v", series, InspectionConfig())
    assert "1/5 finite numeric values" in finding.evidence
    assert "Examples: 10." in finding.evidence
    assert check_outliers("v", series, InspectionConfig(iqr_multiplier=3)) == []


def test_minimum_count_is_configurable_and_counts_only_finite_values():
    series = pd.Series([1, 2, 3, 100, None, np.inf])
    assert len(check_outliers("v", series, InspectionConfig())) == 1
    assert check_outliers("v", series, InspectionConfig(outlier_min_count=5)) == []
    assert len(check_outliers("v", pd.Series([1, 2, 100]),
                              InspectionConfig(outlier_min_count=3, iqr_multiplier=0.5))) == 1


def test_outlier_count_includes_repetitions_but_examples_are_unique_and_limited():
    series = pd.Series([0, 1, 2, 3, 4, 5, 6, 7, 8, 100, 100, 200])
    finding, = check_outliers("v", series, InspectionConfig(top_values=1))
    assert "3/12 finite numeric values" in finding.evidence
    assert "Examples: 100." in finding.evidence
    assert "Examples: 100, 200" not in finding.evidence


def test_extreme_scale_avoids_overflow_and_keeps_outlier_comparison():
    series = pd.Series([1e306, 2e306, 3e306, 4e306, 1e308])
    finding, = check_outliers("v", series, InspectionConfig())
    assert "1/5 finite numeric values" in finding.evidence
    assert "Examples: 1e+308." in finding.evidence
