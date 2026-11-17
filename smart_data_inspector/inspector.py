"""Compose independent Pandas profilers and quality checks; never alter input data."""

from typing import cast

import pandas as pd

from .config import DEFAULT_MISSING_VALUES, InspectionConfig
from .models import ColumnSummary, Dataset, Finding, Inspection, NumericSummary
from .profiling.categorical.profiler import profile_categorical
from .profiling.duplicates.profiler import profile_duplicates
from .profiling.missingness.profiler import normalize_missing, profile_missingness
from .profiling.numeric.profiler import profile_numeric
from .profiling.schema.profiler import profile_schema
from .quality.duplicates.checks import check_duplicates
from .quality.missingness.checks import check_missingness
from .quality.mixed_types.checks import check_mixed_types
from .quality.outliers.checks import check_outliers

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
            unexpected_values=schema.unexpected_values,
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
    try:
        file_size = dataset.source.stat().st_size
    except OSError:
        file_size = None
    return Inspection(dataset, config, columns, duplicates, findings,
                      int(frame.memory_usage(index=True, deep=True).sum()), file_size)
