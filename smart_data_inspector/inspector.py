"""Compose independent Pandas profilers and quality checks; never alter input data."""

from typing import cast

import pandas as pd

from .config import DEFAULT_MISSING_VALUES, InspectionConfig
from .models import ColumnSummary, Dataset, Finding, Inspection, NumericSummary
from .profiling.categorical.profiler import profile_categorical
from .profiling.duplicates.profiler import profile_duplicates
from .profiling.missingness.profiler import normalize_missing, profile_missingness
from .profiling.missingness_analysis import profile_missingness_patterns
from .profiling.numeric.profiler import profile_numeric
from .profiling.relationships import profile_relationships
from .profiling.schema.profiler import profile_schema
from .profiling.text import profile_text
from .quality.duplicates.checks import check_duplicates
from .quality.missingness.checks import check_missingness
from .quality.mixed_types.checks import check_mixed_types
from .quality.outliers.checks import check_outliers
from .quality.numeric import check_numeric_quality
from .quality.relationships import check_relationships
from .quality.schema import check_schema
from .quality.text import check_text_quality

__all__ = ["DEFAULT_MISSING_VALUES", "Inspection", "InspectionConfig", "NumericSummary", "inspect_dataset"]


def inspect_dataset(dataset: Dataset, config: InspectionConfig | None = None) -> Inspection:
    """Profile one loaded table; this reusable API also safely handles zero rows."""
    config = config or InspectionConfig()
    frame = normalize_missing(dataset.to_frame(), config.missing_values)
    duplicates = profile_duplicates(frame)
    findings = check_duplicates(duplicates)
    columns = []
    for name in frame.columns:
        series = cast(pd.Series, frame[name])
        missing = profile_missingness(series)
        schema = profile_schema(series, csv_input=dataset.format == "CSV", config=config)
        categorical = profile_categorical(series, config)
        numeric = profile_numeric(schema.numeric_values) if schema.inferred_type in {"integer", "number", "mixed"} else None
        columns.append(ColumnSummary(
            name=name, inferred_type=schema.inferred_type,
            missing_count=missing.missing_count, missing_fraction=missing.missing_fraction,
            non_null_count=missing.non_null_count, distinct_count=categorical.distinct_count,
            type_counts=schema.type_counts, top_values=categorical.top_values,
            numeric=numeric, likely_identifier=schema.likely_identifier,
            unexpected_values=schema.unexpected_values, text=profile_text(series),
            rare_count=categorical.rare_count, rare_examples=categorical.rare_examples,
        ))
        findings.extend(check_missingness(name, missing, config))
        findings.extend(check_mixed_types(name, schema, config))
        if numeric is not None and numeric.nonfinite_count:
            findings.append(Finding(
                "Non-finite numeric values", name, "warning",
                f"{numeric.nonfinite_count:,} numeric value(s) cannot be represented as finite float64 numbers.",
                "Numeric summaries and IQR checks use finite float64 values only.",
                "Review infinity or magnitudes outside the supported floating-point range; values were excluded, not imputed.",
            ))
        if not schema.likely_identifier:
            findings.extend(check_outliers(name, schema.numeric_values, config))
        findings.extend(check_numeric_quality(columns[-1], config))
        findings.extend(check_text_quality(columns[-1], config))
    missingness = profile_missingness_patterns(frame, config)
    numeric_columns = [column.name for column in columns if column.numeric is not None and not column.likely_identifier]
    relationships = profile_relationships(frame, numeric_columns, config)
    findings.extend(check_schema(frame, columns, config))
    findings.extend(check_relationships(relationships, config))
    try:
        file_size = dataset.source.stat().st_size
    except OSError:
        file_size = None
    severity_order = {"warning": 0, "info": 1}
    findings.sort(key=lambda finding: (severity_order.get(finding.severity, 2), finding.check_name, finding.column or ""))
    return Inspection(dataset, config, columns, duplicates, findings,
                      int(frame.memory_usage(index=True, deep=True).sum()), file_size,
                      missingness, relationships)
