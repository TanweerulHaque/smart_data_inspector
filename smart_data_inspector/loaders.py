"""Public loading API; format-specific parsers live under ingestion/."""

from decimal import DecimalException
from pathlib import Path

from .ingestion.csv.loader import load_csv
from .ingestion.json.loader import load_json
from .models import Dataset, InspectionError, Scalar

__all__ = ["Dataset", "InspectionError", "Scalar", "load_dataset"]


def load_dataset(source: str | Path) -> Dataset:
    """Validate a local CSV/JSON path and load a non-empty table without modifying it."""
    path = Path(source).expanduser()
    suffix = path.suffix.lower()
    if suffix not in {".csv", ".json"}:
        raise InspectionError("Unsupported file extension; use a .csv or .json file (not JSON Lines).")
    if not path.is_file():
        raise InspectionError(f"Input is not a readable file: {str(path)!r}.")
    try:
        columns, rows = load_csv(path) if suffix == ".csv" else load_json(path)
    except UnicodeError as exc:
        raise InspectionError("Input must contain valid UTF-8 text and Unicode scalar values (an optional BOM is supported).") from exc
    except OSError as exc:
        raise InspectionError(f"Cannot read {str(path)!r}: {exc.strerror or exc}.") from exc
    except (DecimalException, ValueError, RecursionError) as exc:
        if isinstance(exc, InspectionError):
            raise
        raise InspectionError(f"Cannot parse input values: {exc}.") from exc
    if not rows or not columns:
        raise InspectionError("Dataset is empty: at least one data row and one column are required.")
    return Dataset(path, suffix[1:].upper(), columns, rows)
