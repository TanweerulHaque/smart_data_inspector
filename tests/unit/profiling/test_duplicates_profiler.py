"""Full-row duplicate counts preserve native scalar type distinctions."""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from smart_data_inspector.profiling.duplicates.profiler import profile_duplicates


@pytest.mark.parametrize(
    "rows, expected",
    [([], 0), ([[1, "a"]], 0), ([[1, "a"], [2, "b"]], 0),
     ([[1, "a"], [1, "a"], [1, "a"]], 2),
     ([[1, "a"], [1, "b"], [1, "a"], [2, "b"], [2, "b"]], 2)],
)
def test_counts_additional_occurrences_of_entire_rows_only(rows, expected):
    frame = pd.DataFrame(rows, columns=["a", "b"], dtype=object)
    before = frame.copy(deep=True)
    assert profile_duplicates(frame) == expected
    assert_frame_equal(frame, before)


def test_booleans_do_not_duplicate_numeric_zero_and_one_but_one_and_float_one_do():
    frame = pd.DataFrame({"v": [True, 1, 1.0, False, 0, 0.0, "1", "0"]}, dtype=object)
    assert profile_duplicates(frame) == 2


def test_csv_original_strings_do_not_duplicate_lexically_equivalent_tokens():
    frame = pd.DataFrame({"v": ["001", "1", "1.0", " TRUE ", "true", "1"]}, dtype=object)
    assert profile_duplicates(frame) == 1


def test_normalized_null_kinds_are_equivalent_but_not_a_literal_marker():
    frame = pd.DataFrame({"v": [None, pd.NA, float("nan"), "NA", ""]}, dtype=object)
    # Marker normalization is a separate step, not an implicit side effect here.
    assert profile_duplicates(frame) == 2


def test_multi_column_signatures_are_not_delimiter_joined_strings():
    frame = pd.DataFrame([["a|b", "c"], ["a", "b|c"], ["a|b", "c"]], columns=["a", "b"])
    assert profile_duplicates(frame) == 1
