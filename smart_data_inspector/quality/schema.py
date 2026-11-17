"""Structural checks that need the whole table rather than one column."""

import re

import pandas as pd

from ..config import InspectionConfig
from ..models import ColumnSummary, Finding
from ..utils.serialization import value_key


def check_schema(frame: pd.DataFrame, columns: list[ColumnSummary],
                 config: InspectionConfig | None = None) -> list[Finding]:
    """Check names, empty columns, and identical column value sequences."""
    del config
    findings: list[Finding] = []
    for column in columns:
        if not str(column.name).strip():
            findings.append(Finding("Invalid column name", column.name, "warning", "Column name is blank or whitespace.",
                                    "Names must contain at least one non-whitespace character.",
                                    "Rename the field before downstream work; blank names are hard to reference."))
        elif re.search(r"[\r\n\t]", str(column.name)):
            findings.append(Finding("Suspicious column name", column.name, "info", "Column name contains control whitespace.",
                                    "Names containing tabs or newlines are hard to use consistently.",
                                    "Confirm this is the intended schema label."))
        if column.inferred_type == "empty":
            findings.append(Finding("All-null column", column.name, "warning", "No non-missing values were observed.",
                                    "Column has zero non-null values after missing-value normalization.",
                                    "Check whether data collection failed or the field is intentionally reserved."))
    signatures: dict[tuple[object, ...], str] = {}
    for name in frame.columns:
        signature = tuple(value_key(value) if not pd.isna(value) else ("missing",) for value in frame[name])
        prior = signatures.get(signature)
        if prior is not None:
            findings.append(Finding("Potential duplicate columns", str(name), "warning",
                                    f"Matches column {prior!r} across {len(frame):,} row(s).",
                                    "All normalized cell values are equal in the current dataset.",
                                    "Confirm whether one field is redundant or whether the equality is accidental."))
        else:
            signatures[signature] = str(name)
    return findings
