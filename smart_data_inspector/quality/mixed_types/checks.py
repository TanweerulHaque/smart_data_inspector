"""Flag incompatible native types or mostly numeric CSV columns with text errors."""

from ...config import InspectionConfig
from ...models import Finding, SchemaProfile


def check_mixed_types(column: str, schema: SchemaProfile, config: InspectionConfig) -> list[Finding]:
    if schema.inferred_type != "mixed":
        return []
    counts = ", ".join(f"{kind}: {count:,}" for kind, count in sorted(schema.type_counts.items()))
    return [Finding(
        "Mixed value types", column, "warning",
        f"Observed {counts}. Representative unexpected values: {schema.unexpected_values!r}.",
        f"Incompatible JSON native types, or CSV numeric proportion >= {config.mixed_numeric_threshold:.0%} "
        "with nonnumeric tokens; boolean/number mixtures are incompatible.",
        "Review unexpected values or inconsistent encoding. Mixed codes can be intentional, not confirmed errors.",
    )]
