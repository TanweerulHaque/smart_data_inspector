"""Missing normalization and counts without invoking the inspection orchestrator."""

import numpy as np
import pandas as pd
import pytest

from smart_data_inspector.profiling.missingness.profiler import (
    normalize_missing,
    profile_missingness,
)


@pytest.mark.parametrize(
    "values, expected",
    [([], (0, 0.0, 0)), ([None, np.nan, pd.NA], (3, 1.0, 0)),
     ([None, 0, False, "ok"], (1, 0.25, 3)), ([0, False], (0, 0.0, 2))],
)
def test_counts_include_all_null_kinds_but_not_zero_or_false(values, expected):
    series = pd.Series(values, dtype=object)
    before = series.copy(deep=True)
    summary = profile_missingness(series)
    assert (summary.missing_count, summary.missing_fraction, summary.non_null_count) == expected
    pd.testing.assert_series_equal(series, before)


def test_normalization_is_in_place_and_preserves_nonmissing_tokens():
    values = [None, np.nan, pd.NA, "", " \t", " NA ", "n/a", "NULL", "null", "NaN",
              0, False, "  keep  ", "001"]
    frame = pd.DataFrame({"value": values, "other": list(range(len(values)))}, dtype=object)
    conversions = normalize_missing(frame)
    assert frame["value"].iloc[:10].isna().all()
    assert frame["value"].iloc[10:].tolist() == [0, False, "  keep  ", "001"]
    assert type(frame["value"].iloc[10]) is int
    assert type(frame["value"].iloc[11]) is bool
    assert frame["other"].tolist() == list(range(len(values)))
    assert conversions == {"value": {"": 2, "NA": 1, "n/a": 1, "NULL": 1, "null": 1, "NaN": 1}}


def test_custom_markers_replace_defaults_trimmed_and_case_sensitive():
    frame = pd.DataFrame({"v": [None, "", " \t", " MISSING ", "Straße", "STRASSE",
                                 "NA", "null", "nan", "none"]}, dtype=object)
    normalize_missing(frame, (" MISSING ", "Straße"))
    assert frame["v"].iloc[:5].isna().all()
    assert frame["v"].iloc[5:].tolist() == ["STRASSE", "NA", "null", "nan", "none"]
    assert profile_missingness(frame["v"]).missing_count == 5


def test_default_markers_keep_case_variants_such_as_sodium():
    frame = pd.DataFrame({"element": ["Na", "NA", "na", "None", "none", "K", " NA "]}, dtype=object)
    assert normalize_missing(frame) == {"element": {"NA": 2}}
    assert frame["element"].tolist() == ["Na", None, "na", "None", "none", "K", None]


def test_pyarrow_string_columns_are_normalized_too():
    frame = pd.DataFrame({"s": pd.array(["a", "NA", ""], dtype=pd.StringDtype("pyarrow"))})
    assert normalize_missing(frame) == {"s": {"NA": 1, "": 1}}
    assert frame["s"].isna().tolist() == [False, True, True]


def test_zero_row_normalization_retains_schema():
    frame = pd.DataFrame(columns=["a", "b"], dtype=object)
    assert normalize_missing(frame) == {}
    assert list(frame.columns) == ["a", "b"]
