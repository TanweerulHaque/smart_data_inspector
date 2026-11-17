"""Strict UTF-8 CSV reading with pyarrow's streaming reader."""

import csv
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.csv as pacsv

from ...models import InspectionError


def _header(path: Path) -> list[str]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        columns = next((row for row in csv.reader(stream) if row), [])
    if not columns or any(not name.strip() for name in columns):
        raise InspectionError("Column names must be non-empty; CSV needs a header row.")
    if len(columns) != len(set(columns)):
        raise InspectionError("Duplicate column names are not supported.")
    return columns


def _quotes_balanced(path: Path) -> bool:
    """pyarrow accepts an unclosed quote at end of file; an odd quote count reveals it."""
    count = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            count += block.count(b'"')
    return count % 2 == 0


def load_csv(path: Path) -> pd.DataFrame:
    """Every value stays text (pyarrow-backed strings) until type inference; ragged rows fail."""
    columns = _header(path)
    if not _quotes_balanced(path):
        raise InspectionError("Invalid CSV: odd number of double quotes; a quoted field is not closed.")
    try:
        reader = pacsv.open_csv(
            path,
            parse_options=pacsv.ParseOptions(newlines_in_values=True),
            convert_options=pacsv.ConvertOptions(
                column_types={name: pa.string() for name in columns}, strings_can_be_null=False),
        )
        table = pa.Table.from_batches(list(reader), schema=reader.schema)
    except pa.ArrowInvalid as exc:
        if "UTF8" in str(exc) or "utf8" in str(exc):
            raise UnicodeError(str(exc)) from exc
        raise InspectionError(f"Invalid CSV: {exc}") from exc
    return table.to_pandas(types_mapper={pa.string(): pd.StringDtype("pyarrow")}.get)
