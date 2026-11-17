"""Flat Parquet tables as Arrow-backed pandas columns (no per-value copies)."""

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ...models import InspectionError


def _check_type(name: str, kind: pa.DataType) -> None:
    if pa.types.is_dictionary(kind):  # e.g. pandas categoricals
        kind = kind.value_type
    if pa.types.is_nested(kind):
        raise InspectionError(
            f"Unsupported nested Parquet column {name!r} ({kind}); only flat scalar columns are supported."
        )
    if (pa.types.is_binary(kind) or pa.types.is_large_binary(kind)
            or pa.types.is_fixed_size_binary(kind) or pa.types.is_binary_view(kind)):
        raise InspectionError(f"Unsupported binary Parquet column {name!r} ({kind}).")


def load_parquet(path: Path) -> pd.DataFrame:
    """Read every column of a flat Parquet file; nested and binary columns are rejected."""
    try:
        with pq.ParquetFile(path) as parquet:
            schema = parquet.schema_arrow
            columns = schema.names
            if any(not name.strip() for name in columns):
                raise InspectionError("Column names must be non-empty.")
            if len(columns) != len(set(columns)):
                raise InspectionError("Duplicate column names are not supported.")
            for field in schema:
                _check_type(field.name, field.type)
            table = parquet.read()
    except (pa.ArrowException, OSError) as exc:
        # Arrow reports some corrupt footers as a bare OSError; real I/O errors carry an errno.
        if isinstance(exc, OSError) and exc.errno is not None:
            raise
        raise InspectionError(f"Invalid Parquet file: {str(exc).strip()}") from exc
    return table.to_pandas(types_mapper=pd.ArrowDtype)
