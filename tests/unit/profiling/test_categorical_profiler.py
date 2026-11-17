"""Frequency summaries and conservative, configurable identifier hints."""

import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from smart_data_inspector.config import InspectionConfig
from smart_data_inspector.profiling.categorical.profiler import (
    is_likely_identifier,
    profile_categorical,
)


@pytest.mark.parametrize("values", [[], [None, pd.NA, float("nan")]])
def test_empty_and_all_null_have_no_categories_or_identifier_hint(values):
    summary = profile_categorical(pd.Series(values, dtype=object, name="id"))
    assert summary.distinct_count == 0
    assert summary.top_values == []
    assert not summary.likely_identifier


def test_top_values_exclude_nulls_limit_entries_and_keep_first_seen_ties():
    series = pd.Series(["b", "a", None, "c", "a", "b", "d"], dtype=object, name="label")
    before = series.copy(deep=True)
    summary = profile_categorical(series, InspectionConfig(top_values=2))
    assert summary.distinct_count == 4
    assert summary.top_values == [("b", 2), ("a", 2)]
    assert not summary.likely_identifier
    assert_series_equal(series, before)


def test_numeric_equivalence_does_not_merge_boolean_or_text_categories():
    summary = profile_categorical(pd.Series([True, 1, 1.0, False, 0, "1", None], dtype=object),
                                  InspectionConfig(top_values=10))
    assert summary.distinct_count == 5
    assert summary.top_values[0][0] == 1
    assert not isinstance(summary.top_values[0][0], (bool, str))
    assert summary.top_values[0][1] == 2
    assert [(type(value), value, count) for value, count in summary.top_values[1:]] == [
        (bool, True, 1), (bool, False, 1), (int, 0, 1), (str, "1", 1),
    ]


@pytest.mark.parametrize("name", ["id", "sample_id", "UUID", "record-key", "guid", "identifier"])
def test_identifier_names_use_non_null_uniqueness_not_total_rows(name):
    series = pd.Series([1, 2, 3, None, None], dtype=object, name=name)
    assert is_likely_identifier(series, InspectionConfig())
    assert profile_categorical(series).likely_identifier


@pytest.mark.parametrize("name", ["grid", "identity", "liquid", "measurement"])
def test_identifier_name_matching_uses_word_boundaries(name):
    assert not is_likely_identifier(pd.Series([1, 2, 3], name=name), InspectionConfig())


def test_named_identifier_uniqueness_threshold_is_inclusive_and_configurable():
    series = pd.Series(list(range(19)) + [0, None], dtype=object, name="sample_id")
    assert is_likely_identifier(series, InspectionConfig())
    assert not is_likely_identifier(series, InspectionConfig(identifier_unique_ratio=0.950001))
    repeated = pd.Series([1, 1, 2, 2], name="id")
    assert not is_likely_identifier(repeated, InspectionConfig())
    assert is_likely_identifier(repeated, InspectionConfig(identifier_unique_ratio=0.5))


def test_unnamed_unique_text_requires_minimum_count_but_unique_numbers_do_not_qualify():
    config = InspectionConfig()
    assert not is_likely_identifier(pd.Series([str(i) for i in range(9)], name="label"), config)
    text = pd.Series([str(i) for i in range(10)] + [None], dtype=object, name="label")
    assert is_likely_identifier(text, config)
    assert not is_likely_identifier(text, InspectionConfig(identifier_min_count=11))
    assert not is_likely_identifier(pd.Series(range(10), name="measurement"), config)
    assert not is_likely_identifier(pd.Series(["a"] * 10, name="label"), config)
