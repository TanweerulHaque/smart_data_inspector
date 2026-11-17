"""Machine-readable report built from the same computed results as the Markdown report."""

from typing import Any

from ... import __version__
from ...models import Inspection
from ...utils.serialization import dumps_json, to_json_safe

SCHEMA_VERSION = 1


def _column(column) -> dict[str, Any]:
    return {
        "name": column.name,
        "inferred_type": column.inferred_type,
        "observed_types": column.type_counts,
        "likely_identifier": column.likely_identifier,
        "missing_count": column.missing_count,
        "missing_fraction": column.missing_fraction,
        "non_null_count": column.non_null_count,
        "distinct_count": column.distinct_count,
        "missing_marker_conversions": column.marker_conversions,
        "top_values": [{"value": value, "count": count} for value, count in column.top_values],
        "rare_count": column.rare_count,
        "rare_examples": column.rare_examples,
        "unexpected_values": column.unexpected_values,
        "numeric": column.numeric,
        "datetime": column.datetime,
        "text": column.text,
    }


def build_json_report(inspection: Inspection) -> dict[str, Any]:
    """Return a JSON-safe dictionary; raw rows are deliberately not included."""
    dataset, columns = inspection.dataset, inspection.columns
    rows = dataset.row_count
    missing = sum(column.missing_count for column in columns)
    cells = rows * len(columns)
    report = {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "smart-data-inspector", "version": __version__},
        "generated_at": inspection.generated_at or None,
        "source": {
            "name": dataset.source.name, "path": str(dataset.source), "format": dataset.format,
            "file_size_bytes": inspection.file_size_bytes,
        },
        "overview": {
            "rows": rows, "columns": len(columns), "column_names": dataset.columns,
            "inferred_types": {column.name: column.inferred_type for column in columns},
            "missing_cells": missing, "total_cells": cells,
            "completeness": 1 - missing / cells if cells else None,
            "duplicate_rows": inspection.duplicate_rows,
            "memory_bytes": inspection.memory_bytes,
            "finding_count": len(inspection.findings),
            "findings_by_severity": {
                level: sum(item.severity == level for item in inspection.findings)
                for level in sorted({item.severity for item in inspection.findings})
            },
        },
        "columns": [_column(column) for column in columns],
        "missingness": inspection.missingness,
        "relationships": inspection.relationships.relationships if inspection.relationships else [],
        "findings": [
            {"check": item.check_name, "column": item.column, "severity": item.severity,
             "evidence": item.evidence, "rule": item.rule, "explanation": item.explanation}
            for item in inspection.findings
        ],
        "charts": {
            "assets": inspection.assets,
            "status": inspection.chart_status,
        },
        "config": inspection.config,
    }
    return to_json_safe(report)


def render_json_report(inspection: Inspection) -> str:
    return dumps_json(build_json_report(inspection), indent=2) + "\n"
