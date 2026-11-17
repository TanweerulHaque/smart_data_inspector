"""Native JSON types and conservative inference of original CSV tokens."""

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from smart_data_inspector.config import InspectionConfig
from smart_data_inspector.profiling.schema.profiler import classify, profile_schema


@pytest.mark.parametrize(
    "value, native, csv",
    [(True, "boolean", "boolean"), (1, "integer", "integer"),
     (1.5, "number", "number"), (np.bool_(False), "boolean", "boolean"),
     (np.int64(1), "integer", "integer"), (np.float64(2.5), "number", "number"),
     ("001", "string", "integer"), (" +12 ", "string", "integer"),
     ("-.5", "string", "number"), ("3e2", "string", "number"),
     (" TRUE ", "string", "boolean"), ("false", "string", "boolean"),
     ("1a", "string", "string"), ("12.3.4", "string", "string")],
)
def test_scalar_classification_only_lexically_infers_csv(value, native, csv):
    assert classify(value) == native
    assert classify(value, csv_input=True) == csv


@pytest.mark.parametrize("csv_input", [False, True])
def test_empty_and_all_null_schema(csv_input):
    for values in ([], [None, pd.NA, np.nan]):
        profile = profile_schema(pd.Series(values, dtype=object), csv_input=csv_input)
        assert profile.inferred_type == "empty"
        assert profile.type_counts == {}
        assert profile.numeric_values.empty
        assert profile.unexpected_values == []
        assert not profile.likely_identifier


@pytest.mark.parametrize("values", [["1", "1.5", "3e2"], ["true", "false"]])
def test_native_json_strings_remain_strings_even_when_all_look_numeric_or_boolean(values):
    profile = profile_schema(pd.Series(values, dtype=object))
    assert profile.inferred_type == "string"
    assert profile.type_counts == {"string": len(values)}
    assert profile.numeric_values.empty
    assert profile.unexpected_values == []


def test_native_mixed_numeric_subset_excludes_boolean_and_quoted_numbers():
    series = pd.Series([1, "2", True, 3.5, False, None], dtype=object, name="measurement")
    before = series.copy(deep=True)
    profile = profile_schema(series)
    assert profile.inferred_type == "mixed"
    assert profile.type_counts == {"integer": 1, "string": 1, "boolean": 2, "number": 1}
    assert profile.numeric_values.tolist() == [1.0, 3.5]
    assert profile.numeric_values.index.tolist() == [0, 3]
    assert profile.unexpected_values == ["2", True, False]
    assert_series_equal(series, before)


@pytest.mark.parametrize("csv_input, values", [(False, [1, 2.5, 3]), (True, ["1", "2.5", "3"])])
def test_integers_and_floats_are_compatible(csv_input, values):
    profile = profile_schema(pd.Series(values, dtype=object), csv_input=csv_input)
    assert profile.inferred_type == "number"
    assert profile.type_counts == {"integer": 2, "number": 1}
    assert profile.numeric_values.tolist() == [1, 2.5, 3]
    assert profile.unexpected_values == []


@pytest.mark.parametrize(
    "values, threshold, expected",
    [(["1", "2", "3", "4", "bad"], 0.8, "mixed"),
     (["1", "2", "3", "4", "bad"], 0.800001, "string"),
     (["1", "2", "3", "A", "B"], 0.8, "string"),
     (["1", "2", "3", "A", "B"], 0.6, "mixed"),
     (["1", "2", "3", "4", "5"], 1, "integer")],
)
def test_numeric_csv_proportion_threshold_is_inclusive_and_configurable(values, threshold, expected):
    profile = profile_schema(pd.Series(values + [None], dtype=object, name="measurement"),
                             csv_input=True, config=InspectionConfig(mixed_numeric_threshold=threshold))
    assert profile.inferred_type == expected
    if expected == "string":
        assert profile.numeric_values.empty
        assert profile.unexpected_values == []
    else:
        assert profile.numeric_values.tolist() == [float(v) for v in values if v.isdigit()]
        assert profile.unexpected_values == [v for v in values if not v.isdigit()]


def test_categorical_codes_are_not_reported_as_damaged_numeric_data():
    profile = profile_schema(pd.Series(["001", "A12", "002", "B03", "A12", None],
                                       dtype=object, name="category"), csv_input=True)
    assert profile.inferred_type == "string"
    assert profile.type_counts == {"integer": 2, "string": 3}
    assert profile.numeric_values.empty
    assert profile.unexpected_values == []


def test_named_identifier_suppresses_mostly_numeric_csv_mixed_inference():
    profile = profile_schema(pd.Series(["1", "2", "3", "4", "A5"], name="sample_id"), csv_input=True)
    assert profile.likely_identifier
    assert profile.inferred_type == "string"
    assert profile.numeric_values.empty
    assert profile.unexpected_values == []


def test_unique_semantic_text_is_a_likely_identifier():
    values = [f"X{i}" for i in range(10)]
    profile = profile_schema(pd.Series(values, name="code"), csv_input=True)
    assert profile.likely_identifier
    assert profile.inferred_type == "string"
    assert profile.numeric_values.empty


@pytest.mark.parametrize("csv_input, values", [(False, [True, 1]), (True, ["true", "1"])])
def test_boolean_and_number_are_incompatible_even_when_values_compare_equal(csv_input, values):
    profile = profile_schema(pd.Series(values, dtype=object), csv_input=csv_input)
    assert profile.inferred_type == "mixed"
    assert profile.type_counts == {"boolean": 1, "integer": 1}
    assert profile.numeric_values.tolist() == [1.0]


def test_unexpected_examples_are_distinct_and_limited():
    profile = profile_schema(pd.Series([1, 2, "bad", "bad", "other", "last"], dtype=object),
                             config=InspectionConfig(top_values=2))
    assert profile.inferred_type == "mixed"
    assert profile.unexpected_values == ["bad", "other"]


def test_native_nonnumeric_mixture_reports_minority_type_example():
    profile = profile_schema(pd.Series(["yes", "no", False], dtype=object))
    assert profile.inferred_type == "mixed"
    assert profile.numeric_values.empty
    assert profile.unexpected_values == [False]
