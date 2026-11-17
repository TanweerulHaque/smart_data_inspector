"""Only row-oriented JSON arrays of flat objects are supported."""

import json
from decimal import Decimal
from pathlib import Path

from ...models import InspectionError, Scalar


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for name, value in pairs:
        if name in result:
            raise InspectionError(f"Duplicate JSON key {name!r} is not supported.")
        result[name] = value
    return result


def _reject_constant(value: str) -> None:
    raise InspectionError(f"JSON contains {value}; use null instead of non-finite numbers.")


def load_json(path: Path) -> tuple[list[str], list[list[Scalar]]]:
    """Retain first-seen column order and substitute None for omitted keys."""
    try:
        with path.open(encoding="utf-8-sig") as stream:
            records = json.load(stream, parse_float=Decimal, parse_constant=_reject_constant,
                                object_pairs_hook=_unique_object)
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
    columns: dict[str, None] = {}
    for index, record in enumerate(records, 1):
        if not isinstance(record, dict):
            raise InspectionError(f"JSON row {index} must be a flat object.")
        for name, value in record.items():
            # JSON escape sequences can encode lone surrogates that UTF-8 cannot represent.
            name.encode("utf-8")
            if isinstance(value, str):
                value.encode("utf-8")
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
