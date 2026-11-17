"""Infer simple types, summarize columns and apply explainable quality rules."""

import re
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, DecimalException
from math import isfinite
from statistics import mean

from .loaders import Dataset, InspectionError, Scalar

DEFAULT_MISSING_VALUES = ("", "na", "n/a", "null", "none", "nan")
INTEGER = re.compile(r"[+-]?[0-9]+\Z")
NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


@dataclass(frozen=True)
class InspectionConfig:
    missing_threshold: float = 0.2
    top_values: int = 3
    missing_values: tuple[str, ...] = DEFAULT_MISSING_VALUES

    def __post_init__(self) -> None:
        if not isfinite(self.missing_threshold) or not 0 < self.missing_threshold <= 1:
            raise ValueError("Missing threshold must be greater than 0 and at most 1.")
        if self.top_values < 1:
            raise ValueError("Top values must be a positive integer.")


@dataclass
class NumericSummary:
    count: int
    minimum: Decimal
    maximum: Decimal
    mean: Decimal


@dataclass
class ColumnSummary:
    name: str
    inferred_type: str
    missing_count: int
    missing_fraction: float
    distinct_count: int
    type_counts: dict[str, int]
    top_values: list[tuple[Scalar, int]]
    numeric: NumericSummary | None


@dataclass
class Finding:
    rule: str
    column: str | None
    message: str


@dataclass
class Inspection:
    dataset: Dataset
    config: InspectionConfig
    columns: list[ColumnSummary]
    duplicate_rows: int
    findings: list[Finding]


def _value_key(value: Scalar) -> tuple:
    """Keep booleans distinct from numbers; Python otherwise equates True and 1."""
    if value is None:
        return ("missing", None)
    if isinstance(value, bool):
        return ("boolean", value)
    if isinstance(value, (int, Decimal)):
        return ("number", value)
    return ("string", value)


def _classify(value: Scalar, csv_input: bool) -> tuple[str, Scalar]:
    if isinstance(value, bool):
        return "boolean", value
    if isinstance(value, int):
        return "integer", value
    if isinstance(value, Decimal):
        return "number", value
    if csv_input and isinstance(value, str):
        text = value.strip()
        if text.lower() in {"true", "false"}:
            return "boolean", text.lower() == "true"
        if INTEGER.fullmatch(text):
            return "integer", Decimal(text)
        if NUMBER.fullmatch(text):
            return "number", Decimal(text)
    return "string", value


def _infer_type(type_counts: dict[str, int]) -> str:
    types = set(type_counts)
    if not types:
        return "empty"
    if types <= {"integer", "number"}:
        return "number" if "number" in types else "integer"
    return next(iter(types)) if len(types) == 1 else "mixed"


def inspect_dataset(dataset: Dataset, config: InspectionConfig | None = None) -> Inspection:
    """Summarize normalized values without changing the loaded dataset."""
    config = config or InspectionConfig()
    markers = {value.strip().casefold() for value in config.missing_values} | {""}
    rows = [
        [
            None if isinstance(value, str) and value.strip().casefold() in markers else value
            for value in row
        ]
        for row in dataset.rows
    ]
    signatures = {tuple(_value_key(value) for value in row) for row in rows}
    duplicate_rows = len(rows) - len(signatures)
    findings = []
    if duplicate_rows:
        findings.append(Finding(
            "Duplicate rows", None,
            f"{duplicate_rows:,} repeated row(s) beyond the first occurrence "
            "after missing-value normalization. Check whether these are intended replicates.",
        ))

    summaries = []
    for index, name in enumerate(dataset.columns):
        present = [row[index] for row in rows if row[index] is not None]
        classified = [_classify(value, dataset.format == "CSV") for value in present]
        type_counts = dict(Counter(kind for kind, _ in classified))
        inferred_type = _infer_type(type_counts)
        missing = len(rows) - len(present)
        counts = Counter(_value_key(value) for value in present)
        top_values = [(key[1], count) for key, count in counts.most_common(config.top_values)]
        try:
            numbers = [
                Decimal(value) for kind, value in classified
                if kind in {"integer", "number"} and isinstance(value, (int, Decimal))
            ]
            numeric = NumericSummary(len(numbers), min(numbers), max(numbers), mean(numbers)) if numbers else None
        except (DecimalException, OverflowError, ValueError) as exc:
            raise InspectionError(f"Cannot summarize numbers in column {name!r}: {exc}.") from exc
        summaries.append(ColumnSummary(
            name=name,
            inferred_type=inferred_type,
            missing_count=missing,
            missing_fraction=missing / len(rows),
            distinct_count=len(counts),
            type_counts=type_counts,
            top_values=top_values,
            numeric=numeric,
        ))
        if missing and missing / len(rows) >= config.missing_threshold:
            findings.append(Finding(
                "High missingness", name,
                f"{missing:,}/{len(rows):,} values are missing ({missing / len(rows):.1%}), "
                f"meeting the {config.missing_threshold:.1%} threshold. "
                "Check collection coverage before relying on this column.",
            ))
        if inferred_type == "mixed":
            observed = ", ".join(f"{kind}: {count:,}" for kind, count in sorted(type_counts.items()))
            findings.append(Finding(
                "Mixed value types", name,
                f"Observed {observed}. Check unexpected tokens or inconsistent encoding; "
                "mixed categorical codes can also be legitimate.",
            ))
    return Inspection(dataset, config, summaries, duplicate_rows, findings)
