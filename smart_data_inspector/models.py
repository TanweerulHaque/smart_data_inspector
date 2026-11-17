"""Shared input and result types; no I/O or profiling runs on import."""

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import pandas as pd

from .config import InspectionConfig

Scalar = str | int | float | Decimal | bool | None


class InspectionError(ValueError):
    """An input cannot be inspected safely."""


@dataclass
class Dataset:
    source: Path
    format: str
    columns: list[str]
    rows: list[list[Scalar]]

    def to_frame(self) -> pd.DataFrame:
        """Retain native scalars and CSV tokens until explicit inference."""
        return pd.DataFrame(self.rows, columns=self.columns, dtype=object)


@dataclass(frozen=True)
class MissingSummary:
    missing_count: int
    missing_fraction: float
    non_null_count: int


@dataclass(frozen=True)
class NumericSummary:
    count: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    median: float | None
    std: float | None
    q1: float | None
    q3: float | None
    nonfinite_count: int = 0


@dataclass(frozen=True)
class CategoricalSummary:
    distinct_count: int
    top_values: list[tuple[Scalar, int]]
    likely_identifier: bool


@dataclass
class SchemaProfile:
    inferred_type: str
    type_counts: dict[str, int]
    numeric_values: pd.Series
    unexpected_values: list[Scalar]
    likely_identifier: bool


@dataclass
class ColumnSummary:
    name: str
    inferred_type: str
    missing_count: int
    missing_fraction: float
    non_null_count: int
    distinct_count: int
    type_counts: dict[str, int]
    top_values: list[tuple[Scalar, int]]
    numeric: NumericSummary | None
    likely_identifier: bool = False
    unexpected_values: list[Scalar] = field(default_factory=list)


@dataclass(frozen=True)
class Finding:
    check_name: str
    column: str | None
    severity: str
    evidence: str
    rule: str
    explanation: str

    @property
    def message(self) -> str:
        return f"{self.evidence} {self.explanation}"


@dataclass
class Inspection:
    dataset: Dataset
    config: InspectionConfig
    columns: list[ColumnSummary]
    duplicate_rows: int
    findings: list[Finding]
    memory_bytes: int
    file_size_bytes: int | None
