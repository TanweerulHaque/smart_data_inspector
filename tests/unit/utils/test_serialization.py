"""Strict JSON conversion preserves missing semantics and representable scalar values."""

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from smart_data_inspector.utils.serialization import dumps_json, to_json_safe, value_key


@pytest.mark.parametrize("value", [None, pd.NA, pd.NaT, float("nan"), float("inf"),
                                   float("-inf"), np.float64("nan"), Decimal("NaN"),
                                   Decimal("Infinity"), Decimal("-Infinity")])
def test_missing_and_special_numbers_are_standard_json_null(value):
    assert to_json_safe(value) is None
    assert dumps_json({"value": value}) == '{"value": null}'


def test_numpy_dataclasses_and_paths_convert_recursively():
    @dataclass
    class Result:
        source: Path
        count: object
        values: object

    result = Result(Path("sample.csv"), np.int64(3), np.array([1, np.nan, np.inf]))
    assert json.loads(dumps_json(result)) == {"source": "sample.csv", "count": 3, "values": [1, None, None]}
    assert to_json_safe({"flag": np.bool_(False), "v": (np.float32(1.5), pd.NA)}) == {"flag": False, "v": [1.5, None]}
    assert to_json_safe(pd.Series([1, pd.NA], dtype=object)) == [1, None]


@pytest.mark.parametrize("value", [Decimal("1e-400"), Decimal("1e400"),
                                   Decimal("9007199254740993.0"), Decimal("1.234567890123456789")])
def test_decimal_values_that_cannot_roundtrip_as_float_are_preserved_as_text(value):
    assert json.loads(dumps_json(value)) == str(value)


@pytest.mark.parametrize("value", [Decimal("0.1"), Decimal("1.25"), Decimal(0), Decimal(123)])
def test_ordinary_decimals_serialize_as_numbers(value):
    assert Decimal(str(json.loads(dumps_json(value)))) == value


def test_boolean_is_not_conflated_with_one_and_missing_keys_are_equivalent():
    assert value_key(True) != value_key(1)
    assert value_key(False) != value_key(0)
    assert value_key(1) == value_key(Decimal("1.0"))
    assert value_key(pd.NA) == value_key(None) == value_key(float("nan"))
