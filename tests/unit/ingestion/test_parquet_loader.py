"""Parquet ingestion returns native scalars and rejects unsupported layouts."""

from datetime import date, datetime, timezone
from decimal import Decimal

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from smart_data_inspector.loaders import load_dataset
from smart_data_inspector.models import InspectionError
from smart_data_inspector.profiling.schema.profiler import classify


def test_parquet_round_trip_returns_native_python_scalars(tmp_path, rows):
    path = tmp_path / "typed.parquet"
    pd.DataFrame({
        "count": [1, 2],
        "ratio": [1.5, np.nan],
        "flag": pd.array([True, None], dtype="boolean"),
        "label": ["a", None],
        "aware": pd.to_datetime(["2024-01-01T10:00:00Z", None]),
        "naive": pd.to_datetime(["2024-01-01 10:00:00", "2024-02-03 04:05:06"]),
        "day": [date(2024, 1, 2), None],
    }).to_parquet(path, index=False)

    dataset = load_dataset(path)

    assert dataset.format == "PARQUET"
    assert dataset.columns == ["count", "ratio", "flag", "label", "aware", "naive", "day"]
    first, second = rows(dataset.frame)
    assert first[:4] == [1, 1.5, True, "a"]
    assert second[:4] == [2, None, None, None]
    assert type(first[0]) is int and type(first[2]) is bool
    assert first[4] == datetime(2024, 1, 1, 10, tzinfo=timezone.utc)
    assert first[4].tzinfo is not None and second[4] is None
    assert first[5] == datetime(2024, 1, 1, 10) and first[5].tzinfo is None
    assert first[6] == date(2024, 1, 2) and second[6] is None


def test_parquet_float_nan_and_decimal_values(tmp_path, rows):
    path = tmp_path / "decimal.parquet"
    pq.write_table(pa.table({"x": pa.array([float("nan"), 2.0]),
                             "price": pa.array([Decimal("1.20"), None])}), path)
    assert rows(load_dataset(path).frame) == [[None, Decimal("1.20")], [2.0, None]]


@pytest.mark.parametrize("column, message", [
    (pa.array([{"a": 1}]), "nested"),
    (pa.array([[1, 2]]), "nested"),
    (pa.array([[("k", 1)]], type=pa.map_(pa.string(), pa.int64())), "nested"),
    (pa.array([b"raw"]), "binary"),
])
def test_parquet_rejects_nested_and_binary_columns(tmp_path, column, message):
    path = tmp_path / "bad.parquet"
    pq.write_table(pa.table({"col": column}), path)
    with pytest.raises(InspectionError, match=message):
        load_dataset(path)


@pytest.mark.parametrize("names, message", [(["a", "a"], "Duplicate"), (["a", " "], "non-empty")])
def test_parquet_rejects_duplicate_and_blank_column_names(tmp_path, names, message):
    path = tmp_path / "names.parquet"
    pq.write_table(pa.table([pa.array([1]), pa.array([2])], names=names), path)
    with pytest.raises(InspectionError, match=message):
        load_dataset(path)


@pytest.mark.parametrize("content", [b"", b"not a parquet file", b"PAR1" + b"x" * 64 + b"\x10\x00\x00\x00PAR1"])
def test_parquet_rejects_corrupt_or_empty_bytes(tmp_path, content):
    path = tmp_path / "corrupt.parquet"
    path.write_bytes(content)
    with pytest.raises(InspectionError, match="Invalid Parquet file"):
        load_dataset(path)


def test_parquet_without_rows_is_an_empty_dataset(tmp_path):
    path = tmp_path / "empty.parquet"
    pd.DataFrame({"a": pd.Series([], dtype="int64")}).to_parquet(path, index=False)
    with pytest.raises(InspectionError, match="Dataset is empty"):
        load_dataset(path)


def test_unsupported_extension_message_mentions_parquet(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text("a\n1\n")
    with pytest.raises(InspectionError, match=r"\.parquet"):
        load_dataset(path)


@pytest.mark.parametrize("value", [
    datetime(2024, 1, 1, 10), datetime(2024, 1, 1, tzinfo=timezone.utc), date(2024, 1, 1),
    pd.Timestamp("2024-01-01 10:00:00.000000001"), np.datetime64("2024-01-01"),
])
def test_classify_native_datetime_values(value):
    assert classify(value) == "datetime"
    assert classify(value, csv_input=True) == "datetime"


def test_parquet_inspection_runs_end_to_end_without_warnings(tmp_path):
    from smart_data_inspector.runner import run_inspection
    path = tmp_path / "demo.parquet"
    pd.DataFrame({"a": [1.0, 2.5, None, 4.0, 9.0], "b": [2, 4, 6, 8, 30], "g": ["x", "y", "x", None, "x"]}).to_parquet(path)
    result = run_inspection(path, tmp_path / "out", report_format="both")
    assert result.inspection.dataset.format == "PARQUET"
    assert result.inspection.relationships.relationships
