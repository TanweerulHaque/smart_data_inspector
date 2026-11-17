"""Central defaults and validated, immutable inspection options."""

from dataclasses import dataclass
from math import isfinite

DEFAULT_MISSING_VALUES = ("", "na", "n/a", "null", "none", "nan")


@dataclass(frozen=True)
class InspectionConfig:
    missing_threshold: float = 0.05
    top_values: int = 5
    missing_values: tuple[str, ...] = DEFAULT_MISSING_VALUES
    iqr_multiplier: float = 1.5
    mixed_numeric_threshold: float = 0.8
    identifier_unique_ratio: float = 0.95
    identifier_min_count: int = 10
    outlier_min_count: int = 4

    def __post_init__(self) -> None:
        for name in ("missing_threshold", "mixed_numeric_threshold", "identifier_unique_ratio"):
            value = getattr(self, name)
            if not isfinite(value) or not 0 < value <= 1:
                raise ValueError(f"{name.replace('_', ' ').capitalize()} must be greater than 0 and at most 1.")
        if not isfinite(self.iqr_multiplier) or self.iqr_multiplier <= 0:
            raise ValueError("IQR multiplier must be finite and greater than 0.")
        for name in ("top_values", "identifier_min_count", "outlier_min_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name.replace('_', ' ').capitalize()} must be a positive integer.")
