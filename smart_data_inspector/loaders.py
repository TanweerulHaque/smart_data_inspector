"""Public loading API; format-specific readers live under ingestion/."""

from decimal import DecimalException
from pathlib import Path

from .ingestion.csv.loader import load_csv
from .ingestion.json.loader import load_json, load_json_lines
from .ingestion.parquet.loader import load_parquet
from .models import Dataset, InspectionError, Scalar

__all__ = ["Dataset", "InspectionError", "Scalar", "load_dataset"]

FORMATS = {".csv": "CSV", ".json": "JSON", ".jsonl": "JSONL", ".ndjson": "JSONL", ".parquet": "PARQUET"}


def load_dataset(source: str | Path, *, flatten_json: bool = False) -> Dataset:
    """Validate a local file path and load a non-empty table without modifying the file.

    ``flatten_json`` only affects JSON and JSON Lines input.
    """
    path = Path(source).expanduser()
    file_format = FORMATS.get(path.suffix.lower())
    if file_format is None:
        raise InspectionError("Unsupported file extension; use .csv, .json, .jsonl/.ndjson or .parquet.")
    if not path.is_file():
        raise InspectionError(f"Input is not a readable file: {str(path)!r}.")
    try:
        if file_format == "CSV":
            frame = load_csv(path)
        elif file_format == "JSON":
            frame = load_json(path, flatten=flatten_json)
        elif file_format == "JSONL":
            frame = load_json_lines(path, flatten=flatten_json)
        else:
            frame = load_parquet(path)
    except UnicodeError as exc:
        raise InspectionError("Input must contain valid UTF-8 text and Unicode scalar values (an optional BOM is supported).") from exc
    except OSError as exc:
        raise InspectionError(f"Cannot read {str(path)!r}: {exc.strerror or exc}.") from exc
    except (DecimalException, ValueError, RecursionError) as exc:
        if isinstance(exc, InspectionError):
            raise
        raise InspectionError(f"Cannot parse input values: {exc}.") from exc
    if frame.empty or not len(frame.columns):
        raise InspectionError("Dataset is empty: at least one data row and one column are required.")
    return Dataset(path, file_format, frame)
