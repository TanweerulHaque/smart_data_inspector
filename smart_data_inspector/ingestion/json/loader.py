"""JSON loading: a streamed top-level array of objects, or JSON Lines; optional flattening."""

import json
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import ijson
import pandas as pd

from ...models import InspectionError

MAX_JSON_BYTES = 1024 ** 3
CHUNK_ROWS = 10_000
FLATTEN_HINT = "Re-run with --flatten-json to flatten nested objects."


class _Record(dict):
    """A dict that remembers a repeated key instead of silently overwriting it."""
    duplicate: str | None = None

    def __setitem__(self, key, value):
        if key in self and self.duplicate is None:
            self.duplicate = key
        super().__setitem__(key, value)


def _from_pairs(pairs: list[tuple[str, object]]) -> _Record:
    record = _Record()
    for key, value in pairs:
        record[key] = value
    return record


def _reject_constant(value: str) -> None:
    raise InspectionError(f"JSON contains {value}; use null instead of non-finite numbers.")


def _add(record: dict, index: int, prefix: str, row: dict, flatten: bool) -> None:
    """Copy one record into a flat row; nested objects become dotted columns when flattening."""
    if getattr(record, "duplicate", None) is not None:
        raise InspectionError(f"Duplicate JSON key {record.duplicate!r} in row {index} is not supported.")
    for name, value in record.items():
        name.encode("utf-8")  # lone surrogates take the UnicodeError path
        if not name.strip():
            raise InspectionError(f"JSON row {index} has an empty column name.")
        column = prefix + name
        if flatten and isinstance(value, dict) and value:
            _add(value, index, column + ".", row, flatten)
            continue
        if isinstance(value, (dict, list)):
            if not flatten:
                raise InspectionError(f"Unsupported nested value in JSON row {index}, column {name!r}. "
                                      f"Only flat objects with scalar values are supported. {FLATTEN_HINT}")
            value = json.dumps(value, separators=(",", ":"), ensure_ascii=False, default=float)
        if isinstance(value, str):
            value.encode("utf-8")
        if column in row:
            raise InspectionError(f"JSON row {index}: flattened column name {column!r} is ambiguous.")
        row[column] = value


def _rows(records: Iterator[tuple[str | None, object]], flatten: bool) -> Iterator[dict]:
    for index, (key, record) in enumerate(records, 1):
        if not isinstance(record, dict):
            raise InspectionError(f"JSON row {index} is not {'an' if flatten else 'a flat'} object.")
        row: dict = {}
        if key is not None:
            key.encode("utf-8")
            if "_key" in record:
                raise InspectionError(f"JSON row {index} already has a '_key' field; cannot add the mapping key.")
            row["_key"] = key
        _add(record, index, "", row, flatten)
        yield row


def _frame(rows: Iterator[dict]) -> pd.DataFrame:
    """Build the table in chunks; keys missing from a row become missing values."""
    chunks, batch = [], []
    for row in rows:
        batch.append(row)
        if len(batch) == CHUNK_ROWS:
            chunks.append(pd.DataFrame(batch, dtype=object))
            batch = []
    if batch:
        chunks.append(pd.DataFrame(batch, dtype=object))
    return pd.concat(chunks, ignore_index=True, sort=False) if chunks else pd.DataFrame()


def _first_character(path: Path) -> str:
    with path.open("rb") as stream:
        return stream.read(4096).lstrip(b"\xef\xbb\xbf \t\r\n")[:1].decode("ascii", "replace")


def _array_records(path: Path, flatten: bool) -> Iterator[tuple[str | None, object]]:
    first = _first_character(path)
    if first not in "[{" or not first:
        raise InspectionError("Unsupported JSON: expected a top-level array of flat objects.")
    if first == "{" and not flatten:
        raise InspectionError("Unsupported JSON: expected a top-level array of flat objects, not an object "
                              f"mapping. Use JSON Lines for one record per line. {FLATTEN_HINT}")
    with path.open("rb") as stream:
        if stream.read(3) != b"\xef\xbb\xbf":
            stream.seek(0)
        try:
            if first == "[":
                for record in ijson.items(stream, "item", map_type=_Record):
                    yield None, record
            else:
                yield from ijson.kvitems(stream, "", map_type=_Record)
        except ijson.JSONError as exc:
            message = str(exc).splitlines()[0]
            raise InspectionError(f"Invalid JSON: {message}. Expected one array of objects "
                                  "(use a .jsonl extension for JSON Lines).") from exc


def _line_records(path: Path) -> Iterator[tuple[None, object]]:
    with path.open(encoding="utf-8-sig") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                yield None, json.loads(line, parse_float=Decimal, parse_constant=_reject_constant,
                                       object_pairs_hook=_from_pairs)
            except json.JSONDecodeError as exc:
                raise InspectionError(f"Invalid JSON Lines record on line {number}: {exc.msg}.") from exc


def load_json(path: Path, flatten: bool = False) -> pd.DataFrame:
    """Stream a top-level array of objects (or, when flattening, an object of records)."""
    size = path.stat().st_size
    if size > MAX_JSON_BYTES:
        raise InspectionError(f"JSON file is {size / 1024 ** 3:.1f} GiB, above the {MAX_JSON_BYTES / 1024 ** 3:.0f} GiB "
                              "limit for JSON arrays. Convert it to JSON Lines (.jsonl), CSV or Parquet.")
    return _frame(_rows(_array_records(path, flatten), flatten))


def load_json_lines(path: Path, flatten: bool = False) -> pd.DataFrame:
    """One JSON object per line; the cheap path for large files."""
    return _frame(_rows(_line_records(path), flatten))
