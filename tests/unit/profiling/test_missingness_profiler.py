"""Missing normalization and counts without invoking the inspection orchestrator."""

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

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


def test_normalization_returns_independent_frame_and_preserves_nonmissing_tokens():
    values = [None, np.nan, pd.NA, "", " \t", " NA ", "n/A", "NULL", "none", "NaN",
              0, False, "  keep  ", "001"]
    frame = pd.DataFrame({"value": values, "other": list(range(len(values)))}, dtype=object)
    before = frame.copy(deep=True)
    normalized = normalize_missing(frame)
    assert normalized is not frame
    assert normalized["value"].iloc[:10].isna().all()
    assert normalized["value"].iloc[10:].tolist() == [0, False, "  keep  ", "001"]
    assert type(normalized["value"].iloc[10]) is int
    assert type(normalized["value"].iloc[11]) is bool
    assert normalized["other"].tolist() == list(range(len(values)))
    assert_frame_equal(frame, before)
    normalized.loc[0, "other"] = "changed"
    assert_frame_equal(frame, before)


def test_custom_markers_replace_defaults_and_use_trimmed_unicode_casefold():
    frame = pd.DataFrame({"v": [None, "", " \t", " MISSING ", "Straße", "STRASSE",
                                 "NA", "null", "nan", "none"]}, dtype=object)
    normalized = normalize_missing(frame, (" missing ", "strasse"))
    series = normalized["v"]
    assert isinstance(series, pd.Series)
    assert series.iloc[:6].isna().all()
    assert series.iloc[6:].tolist() == ["NA", "null", "nan", "none"]
    assert profile_missingness(series).missing_count == 6


def test_zero_row_normalization_retains_schema():
    frame = pd.DataFrame(columns=["a", "b"], dtype=object)
    assert_frame_equal(normalize_missing(frame), frame)
