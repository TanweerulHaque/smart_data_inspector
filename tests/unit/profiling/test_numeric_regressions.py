"""Regressions for review-discovered float extremes and CSV identifier ambiguity."""

from itertools import permutations
from pathlib import Path

import pandas as pd
import pytest

from smart_data_inspector.config import InspectionConfig
from smart_data_inspector.inspector import inspect_dataset
from smart_data_inspector.models import Dataset, Scalar
from smart_data_inspector.profiling.numeric.profiler import profile_numeric
from smart_data_inspector.profiling.schema.profiler import profile_schema
from smart_data_inspector.quality.outliers.checks import check_outliers


def test_wide_magnitude_range_preserves_representable_tiny_quartiles():
    series = pd.Series([1e-200, 2e-200, 3e-200, 4e-200, 1e308])
    numeric = profile_numeric(series)
    assert numeric.q1 == pytest.approx(2e-200, rel=1e-14, abs=0)
    assert numeric.median == pytest.approx(3e-200, rel=1e-14, abs=0)
    assert numeric.q3 == pytest.approx(4e-200, rel=1e-14, abs=0)
    finding, = check_outliers("measurement", series, InspectionConfig())
    assert "1/5" in finding.evidence
    assert "1e+308" in finding.evidence


@pytest.mark.parametrize("values", sorted(set(permutations([1e308, 1e308, 1, -1e308, -1e308]))))
def test_cancellation_after_sum_overflow_is_not_row_order_dependent(values):
    assert profile_numeric(pd.Series(values)).mean == pytest.approx(0.2)


@pytest.mark.parametrize("format", ["CSV", "JSON"])
def test_unique_measurements_are_not_identifier_columns_and_outliers_are_checked(format):
    values = list(range(1, 10)) + [100]
    rows: list[list[Scalar]] = [[str(value) if format == "CSV" else value] for value in values]
    result = inspect_dataset(Dataset.from_rows(Path("input." + format.lower()), format, ["measurement"], rows))
    assert not result.columns[0].likely_identifier
    assert any(f.check_name == "Potential numerical outliers" for f in result.findings)


def test_unique_mostly_numeric_csv_is_still_checked_for_inconsistent_types():
    schema = profile_schema(pd.Series([str(i) for i in range(9)] + ["bad"], name="measurement"), True)
    assert not schema.likely_identifier
    assert schema.inferred_type == "mixed"
    assert schema.unexpected_values == ["bad"]


@pytest.mark.parametrize("value", [10**309, str(10**309), "1e309", "-1e309", -(10**309)])
def test_magnitudes_outside_float64_are_excluded_with_explicit_warning(value):
    format = "CSV" if isinstance(value, str) else "JSON"
    result = inspect_dataset(Dataset.from_rows(Path("input." + format.lower()), format, ["v"], [[value], [1]]))
    numeric = result.columns[0].numeric
    assert numeric is not None
    assert (numeric.count, numeric.nonfinite_count, numeric.mean) == (1, 1, 1)
    assert any(f.check_name == "Non-finite numeric values" for f in result.findings)
