"""Conservative scalar type inference without treating categorical codes as errors."""

import re
from decimal import Decimal
from typing import cast

import numpy as np
import pandas as pd

from ...config import InspectionConfig
from ...models import SchemaProfile
from ...utils.numeric import as_numeric_series
from ..categorical.profiler import is_likely_identifier

INTEGER = re.compile(r"[+-]?[0-9]+\Z")
NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


def classify(value: object, csv_input: bool = False) -> str:
    """JSON strings stay strings; only CSV tokens undergo lexical inference."""
    if isinstance(value, (bool, np.bool_)):
        return "boolean"
    if isinstance(value, (int, np.integer)):
        return "integer"
    if isinstance(value, (float, Decimal, np.floating)):
        return "number"
    if csv_input and isinstance(value, str):
        text = value.strip()
        if text.casefold() in {"true", "false"}:
            return "boolean"
        if INTEGER.fullmatch(text):
            return "integer"
        if NUMBER.fullmatch(text) or text.casefold() in {"inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
            return "number"
    return "string"


def profile_schema(series: pd.Series, csv_input: bool = False,
                   config: InspectionConfig | None = None) -> SchemaProfile:
    """Infer a semantic type, numeric subset and incompatible-value examples."""
    config = config or InspectionConfig()
    present = series.dropna()
    kinds = present.map(lambda value: classify(value, csv_input))
    counts = {str(kind): int(count) for kind, count in kinds.value_counts(sort=False).items()}
    types = set(counts)
    numeric_mask = kinds.isin(["integer", "number"])
    identifier = is_likely_identifier(series, config, text_values=types == {"string"})
    unexpected = []
    if not types:
        inferred = "empty"
    elif types <= {"integer", "number"}:
        inferred = "number" if "number" in types else "integer"
    elif len(types) == 1:
        inferred = next(iter(types))
    elif csv_input and types <= {"integer", "number", "string"}:
        # Sparse numeric-looking category codes are not evidence of a damaged numeric column.
        dominant_numeric = float(numeric_mask.mean()) >= config.mixed_numeric_threshold
        inferred = "mixed" if dominant_numeric and not identifier else "string"
    else:
        inferred = "mixed"
    if inferred == "mixed":
        if numeric_mask.any():
            unexpected = cast(pd.Series, present[~numeric_mask]).drop_duplicates().iloc[:config.top_values].tolist()
        else:
            dominant = kinds.value_counts().index[0]
            unexpected = cast(pd.Series, present[kinds != dominant]).drop_duplicates().iloc[:config.top_values].tolist()
    numeric = pd.Series(dtype="float64", name=series.name)
    if inferred in {"integer", "number", "mixed"}:
        # Preserve native numerics until conversion, but do not coerce textual JSON numbers.
        numeric = as_numeric_series(cast(pd.Series, present[numeric_mask]))
    return SchemaProfile(inferred, counts, numeric, unexpected, identifier)
