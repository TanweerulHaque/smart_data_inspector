"""Mixed-type decisions use semantic schema, not observed type count alone."""

import copy

import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from smart_data_inspector.config import InspectionConfig
from smart_data_inspector.models import SchemaProfile
from smart_data_inspector.quality.mixed_types.checks import check_mixed_types


@pytest.mark.parametrize(
    "inferred, counts, identifier",
    [("empty", {}, False), ("integer", {"integer": 4}, False),
     ("number", {"integer": 2, "number": 2}, False),
     ("boolean", {"boolean": 4}, False),
     ("string", {"integer": 2, "string": 3}, False),
     ("string", {"integer": 4, "string": 1}, True)],
)
def test_nonmixed_semantics_do_not_flag_compatible_numbers_or_categorical_codes(inferred, counts, identifier):
    schema = SchemaProfile(inferred, counts, pd.Series(dtype=float), [], identifier)
    assert check_mixed_types("v", schema, InspectionConfig()) == []


def test_mixed_finding_explains_types_examples_and_configured_threshold_without_mutation():
    schema = SchemaProfile("mixed", {"integer": 4, "string": 1},
                           pd.Series([1.0, 2, 3, 4]), ["bad"], False)
    before = copy.deepcopy(schema)
    findings = check_mixed_types("measurement", schema, InspectionConfig(mixed_numeric_threshold=0.9))
    assert len(findings) == 1
    finding = findings[0]
    assert (finding.check_name, finding.column, finding.severity) == (
        "Mixed value types", "measurement", "warning",
    )
    assert "integer: 4" in finding.evidence
    assert "string: 1" in finding.evidence
    assert "['bad']" in finding.evidence
    assert ">= 90%" in finding.rule
    assert "boolean/number mixtures are incompatible" in finding.rule
    assert "not confirmed errors" in finding.explanation
    assert schema.type_counts == before.type_counts
    assert schema.unexpected_values == before.unexpected_values
    assert_series_equal(schema.numeric_values, before.numeric_values)


def test_native_boolean_numeric_mixture_is_reported_even_if_numerically_equal():
    schema = SchemaProfile("mixed", {"boolean": 1, "integer": 1}, pd.Series([1.0]), [True], False)
    finding, = check_mixed_types("v", schema, InspectionConfig())
    assert finding.check_name == "Mixed value types"
    assert "boolean: 1" in finding.evidence
    assert "[True]" in finding.evidence
