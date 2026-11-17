"""Duplicate findings distinguish check identity, evidence and comparison rule."""

import pytest

from smart_data_inspector.quality.duplicates.checks import check_duplicates


def test_no_duplicates_has_no_finding():
    assert check_duplicates(0) == []


@pytest.mark.parametrize("count, formatted", [(1, "1"), (1234, "1,234")])
def test_duplicate_finding_is_dataset_scoped_and_does_not_recommend_blind_removal(count, formatted):
    findings = check_duplicates(count)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.check_name == "Duplicate rows"
    assert finding.column is None
    assert finding.severity == "warning"
    assert f"{formatted} repeated row(s) beyond the first occurrence" in finding.evidence
    assert "Full-row equality" in finding.rule
    assert "missing-value normalization" in finding.rule
    assert "additional occurrences only" in finding.rule
    assert "intended replicates" in finding.explanation
