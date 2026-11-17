"""Strict UTF-8 CSV parsing before Pandas inference."""

import csv
from pathlib import Path

from ...models import InspectionError, Scalar


def load_csv(path: Path) -> tuple[list[str], list[list[Scalar]]]:
    """Read a header and rectangular records without silently skipping malformed rows."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        try:
            columns = next((row for row in reader if row), [])
            if not columns or any(not name.strip() for name in columns):
                raise InspectionError("Column names must be non-empty; CSV needs a header row.")
            if len(columns) != len(set(columns)):
                raise InspectionError("Duplicate column names are not supported.")
            rows = []
            for row in reader:
                if not row:
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
