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
    """A loaded table. ``frame`` may be released (set to None) once profiling is done."""
    source: Path
    format: str
    frame: pd.DataFrame | None
    columns: list[str] = field(init=False)
    row_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.columns = [str(name) for name in self.frame.columns]
        self.row_count = len(self.frame)

    @classmethod
    def from_rows(cls, source: Path, format: str, columns: list[str], rows: list[list[Scalar]]) -> "Dataset":
        return cls(source, format, pd.DataFrame(rows, columns=columns, dtype=object))


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
    variance: float | None = None
    mode: float | None = None
    skewness: float | None = None
    kurtosis: float | None = None
    zero_count: int = 0
    zero_fraction: float = 0.0


@dataclass(frozen=True)
class CategoricalSummary:
    distinct_count: int
    top_values: list[tuple[Scalar, int]]
    likely_identifier: bool
    rare_count: int = 0
    rare_examples: list[Scalar] = field(default_factory=list)


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
    text: "TextSummary | None" = None
    rare_count: int = 0
    rare_examples: list[Scalar] = field(default_factory=list)
    datetime: "DatetimeSummary | None" = None
    marker_conversions: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class DatetimeSummary:
    """Parsed date/time evidence; naive values are compared as UTC."""
    count: int
    invalid_count: int
    invalid_examples: list[str]
    minimum: str | None
    maximum: str | None
    span_days: float | None
    future_count: int
    future_examples: list[str]
    reference_time: str
    formats: dict[str, int]
    timezone_aware_count: int
    naive_count: int
    non_iso_count: int = 0
    non_iso_examples: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TextSummary:
    """Compact string evidence used by narrative and formatting checks."""
    count: int
    empty_count: int
    whitespace_count: int
    casefold_collision_count: int
    minimum_length: int | None
    maximum_length: int | None
    mean_length: float | None


@dataclass(frozen=True)
class MissingPattern:
    columns: tuple[str, ...]
    count: int


@dataclass(frozen=True)
class MissingnessProfile:
    total_missing: int
    total_cells: int
    row_missing_counts: list[int]
    high_missing_rows: int
    patterns: list[MissingPattern]
    cooccurrences: list[tuple[str, str, int]]


@dataclass(frozen=True)
class Relationship:
    left: str
    right: str
    pearson: float | None
    spearman: float | None
    pair_count: int


@dataclass(frozen=True)
class RelationshipProfile:
    relationships: list[Relationship]
    numeric_columns: list[str]


@dataclass(frozen=True)
class ChartAsset:
    key: str
    relative_path: str
    caption: str


@dataclass(frozen=True)
class ChartStatus:
    """Why each optional chart is, or is not, part of a report."""
    key: str
    title: str
    status: str  # generated | not applicable | failed | disabled
    detail: str = ""


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
    missingness: MissingnessProfile | None = None
    relationships: RelationshipProfile | None = None
    assets: list[ChartAsset] = field(default_factory=list)
    chart_status: list[ChartStatus] = field(default_factory=list)
    generated_at: str = ""
