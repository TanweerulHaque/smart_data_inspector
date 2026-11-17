"""Read UTF-8 CSV and flat, row-oriented JSON without dropping bad records."""

import csv
import json
from dataclasses import dataclass
from decimal import Decimal, DecimalException
from pathlib import Path

Scalar = str | int | Decimal | bool | None


class InspectionError(ValueError):
    """An input cannot be inspected safely."""


@dataclass
class Dataset:
    source: Path
    format: str
    columns: list[str]
    rows: list[list[Scalar]]


def _validate_columns(columns: list[str]) -> None:
    if not columns or any(not name.strip() for name in columns):
        raise InspectionError("Column names must be non-empty; CSV needs a header row.")
    if len(columns) != len(set(columns)):
        raise InspectionError("Duplicate column names are not supported.")


def _load_csv(path: Path) -> tuple[list[str], list[list[Scalar]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        try:
            columns = next((row for row in reader if row), [])
            _validate_columns(columns)
            rows = []
            for row in reader:
                if not row:  # Ignore blank physical lines, not records of empty fields.
                    continue
                if len(row) != len(columns):
                    raise InspectionError(
                        f"CSV record ending at line {reader.line_num} has {len(row)} "
                        f"fields; expected {len(columns)}."
                    )
                rows.append(row)
        except csv.Error as exc:
            raise InspectionError(f"Invalid CSV near line {reader.line_num}: {exc}") from exc
    return columns, rows


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for name, value in pairs:
        if name in result:
            raise InspectionError(f"Duplicate JSON key {name!r} is not supported.")
        result[name] = value
    return result


def _reject_constant(value: str) -> None:
    raise InspectionError(f"JSON contains {value}; use null instead of non-finite numbers.")


def _load_json(path: Path) -> tuple[list[str], list[list[Scalar]]]:
    try:
        with path.open(encoding="utf-8-sig") as stream:
            records = json.load(
                stream,
                parse_float=Decimal,
                parse_constant=_reject_constant,
                object_pairs_hook=_unique_object,
            )
    except json.JSONDecodeError as exc:
        raise InspectionError(
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}. "
            "Expected one array of flat objects, not JSON Lines."
        ) from exc
    if not isinstance(records, list):
        raise InspectionError(
            "Unsupported JSON: expected a top-level array of flat objects. "
            "Object mappings, nested structures and JSON Lines are not supported."
        )
    columns = {}
    for index, record in enumerate(records, 1):
        if not isinstance(record, dict):
            raise InspectionError(f"JSON row {index} must be a flat object.")
        for name, value in record.items():
            if not name.strip():
                raise InspectionError(f"JSON row {index} has an empty column name.")
            if isinstance(value, (dict, list)):
                raise InspectionError(
                    f"Unsupported nested value in JSON row {index}, column {name!r}. "
                    "Only flat objects with scalar values are supported."
                )
            columns.setdefault(name, None)
    names = list(columns)
    return names, [[record.get(name) for name in names] for record in records]


def load_dataset(source: str | Path) -> Dataset:
    """Load a non-empty table, preserving column order and original scalar values."""
    path = Path(source).expanduser()
    suffix = path.suffix.lower()
    if suffix not in {".csv", ".json"}:
        raise InspectionError("Unsupported file extension; use a .csv or .json file.")
    if not path.is_file():
        raise InspectionError(f"Input is not a readable file: {str(path)!r}.")
    try:
        columns, rows = _load_csv(path) if suffix == ".csv" else _load_json(path)
    except UnicodeError as exc:
        raise InspectionError("Input must be UTF-8 encoded (an optional BOM is supported).") from exc
    except OSError as exc:
        raise InspectionError(f"Cannot read {str(path)!r}: {exc.strerror or exc}.") from exc
    except (DecimalException, ValueError) as exc:
        if isinstance(exc, InspectionError):
            raise
        raise InspectionError(f"Cannot parse input values: {exc}.") from exc
    if not rows or not columns:
        raise InspectionError("Dataset is empty: at least one data row and one column are required.")
    return Dataset(path, suffix[1:].upper(), columns, rows)
