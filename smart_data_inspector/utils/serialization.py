"""Stable scalar comparison and strict JSON-safe conversion."""

import json
import math
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def value_key(value: Any) -> tuple:
    """Do not conflate booleans with numeric 0/1 when counting values or rows."""
    if value is None or value is pd.NA or value is pd.NaT:
        return ("missing", None)
    if isinstance(value, (bool, np.bool_)):
        return ("boolean", bool(value))
    if isinstance(value, (int, float, Decimal, np.number)):
        if bool(pd.isna(value)):
            return ("missing", None)
        return ("number", value)
    return ("string", value)


def value_keys(series: pd.Series) -> pd.Series:
    """Vectorised value_key: pure string columns already compare correctly as themselves."""
    return series if pd.api.types.is_string_dtype(series) else series.map(value_key)


def to_json_safe(value: Any) -> Any:
    """Convert dataclasses and NumPy scalars; unavailable/nonfinite values become null."""
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: to_json_safe(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, np.ndarray, pd.Series)):
        return [to_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return to_json_safe(value.item())
    if isinstance(value, Decimal):
        if not value.is_finite():
            return None
        converted = float(value)
        return converted if math.isfinite(converted) and Decimal(str(converted)) == value else str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)  # dates, times and other scalars become readable text


def dumps_json(value: Any, **kwargs: Any) -> str:
    """Serialize without the nonstandard JSON NaN/Infinity constants."""
    return json.dumps(to_json_safe(value), allow_nan=False, ensure_ascii=False, **kwargs)
