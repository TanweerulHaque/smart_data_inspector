"""Quality checks consume summaries directly, without profiling or file I/O."""

import pytest

from smart_data_inspector.config import InspectionConfig
from smart_data_inspector.models import MissingSummary
from smart_data_inspector.quality.missingness.checks import check_missingness


@pytest.mark.parametrize("summary", [MissingSummary(0, 0.0, 0), MissingSummary(0, 0.0, 20)])
def test_zero_missing_has_no_finding_including_zero_rows(summary):
    assert check_missingness("v", summary, InspectionConfig()) == []


@pytest.mark.parametrize(
    "threshold, fraction, expected_name, severity",
    [(0.05, 0.05, "High missingness", "warning"),
     (0.050001, 0.05, "Missing values", "info"),
     (0.2, 0.05, "Missing values", "info"),
     (1, 1.0, "High missingness", "warning")],
)
def test_inclusive_threshold_changes_severity_without_hiding_missing_values(
    threshold, fraction, expected_name, severity,
):
    missing, present = (20, 0) if fraction == 1 else (1, 19)
    findings = check_missingness("measurement", MissingSummary(missing, fraction, present),
                                 InspectionConfig(missing_threshold=threshold))
    assert len(findings) == 1
    finding = findings[0]
    assert (finding.check_name, finding.column, finding.severity) == (expected_name, "measurement", severity)
    assert f"{missing} missing of 20" in finding.evidence
    assert f"{fraction:.2%}" in finding.evidence
    assert ">=" in finding.rule
    assert f"{threshold:.1%}" in finding.rule
    assert "no imputation" in finding.explanation


def test_marker_conversions_are_reported_and_short_codes_are_flagged_as_ambiguous():
    import pandas as pd

    from smart_data_inspector.quality.missingness.checks import check_marker_conversions
    (plain,) = check_marker_conversions("status", {"N/A": 2, "": 1}, pd.Series(["ok", "failed"]))
    assert plain.check_name == "Missing-value markers converted" and "'N/A' ×2" in plain.evidence
    (ambiguous,) = check_marker_conversions("element", {"NA": 1}, pd.Series(["K", "Cl", "Fe"]))
    assert ambiguous.check_name == "Ambiguous missing-value marker" and ambiguous.severity == "warning"
    assert check_marker_conversions("x", {"": 3}, pd.Series(["a"])) == []
