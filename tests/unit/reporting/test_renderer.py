"""Narrative-report contracts: rendering consumes structured results only."""

from pathlib import Path

from smart_data_inspector.config import InspectionConfig
from smart_data_inspector.models import ChartAsset, ColumnSummary, Dataset, Finding, Inspection, NumericSummary
from smart_data_inspector.report import render_report


def make_inspection() -> Inspection:
    numeric = NumericSummary(4, 1, 100, 27.5, 2.5, 48.34, 1.75, 27.25, skewness=1.9, zero_count=0)
    columns = [
        ColumnSummary("sample_id", "string", 0, 0, 4, 4, {"string": 4}, [], None, likely_identifier=True),
        ColumnSummary("reading", "number", 0, 0, 4, 4, {"integer": 4}, [(1, 1)], numeric),
        ColumnSummary("group", "string", 1, 0.25, 3, 2, {"string": 3}, [("control", 2), ("test", 1)], None),
    ]
    dataset = Dataset.from_rows(Path("/input/study.csv"), "CSV", [item.name for item in columns], [["A", 1, "control"], ["B", 2, "control"], ["C", 7, "test"], ["D", 100, None]])
    return Inspection(dataset, InspectionConfig(), columns, 0, [
        Finding("High missingness", "group", "warning", "1 missing of 4 values (25.00%).", "fraction >= 5%", "Review collection coverage."),
        Finding("Potential numerical outliers", "reading", "info", "1/4 values outside fences.", "IQR fence", "Potential, not confirmed errors."),
    ], 2048, 512, assets=[ChartAsset("missingness", "../assets/run/missingness.png", "Columns ranked by missingness.")])


def test_first_page_has_required_researcher_summary_and_priority_findings():
    report = render_report(make_inspection())
    first_chapter = report.split("## Schema inventory", 1)[0]
    assert "## Overview" in first_chapter
    assert "Overall completeness" in first_chapter
    assert "Exact duplicate records" in first_chapter
    assert "Priority observations" in first_chapter
    assert "High missingness" in first_chapter
    assert "Initial assessment" in first_chapter


def test_narrative_chapters_appendix_and_chart_reference_are_present():
    report = render_report(make_inspection())
    for text in ("Chapter 1: Understanding", "Chapter 2: Can I rely", "Chapter 3: What do the measurements", "Chapter 4: Are the categorical", "Chapter 5: How do variables", "Chapter 6: What should concern", "Chapter 7: Recommended", "Chapter 8: Methodology", "Technical appendix"):
        assert text in report
    assert "../assets/run/missingness.png" in report


def test_quality_findings_keep_rule_evidence_and_interpretation():
    report = render_report(make_inspection())
    assert "**Detected:** 1 missing of 4 values" in report
    assert "**Rule:** fraction &gt;= 5%" in report
    assert "**Why investigate:** Review collection coverage." in report


def test_rendering_is_pure_and_escapes_untrusted_markdown():
    inspection = make_inspection()
    inspection.columns[2].name = "bad|*field*\n## injected"
    before = inspection.columns[2].name
    report = render_report(inspection)
    assert "bad\\|\\*field\\*\\n## injected" in report
    assert inspection.columns[2].name == before


def test_detail_sections_cover_mode_text_patterns_and_charts():
    from smart_data_inspector.models import ChartStatus, MissingnessProfile, MissingPattern, TextSummary
    inspection = make_inspection()
    inspection.columns[2].text = TextSummary(3, 0, 1, 0, 4, 7, 5.5)
    inspection.missingness = MissingnessProfile(1, 12, [0, 0, 0, 1], 0, [MissingPattern(("group",), 1)], [])
    inspection.chart_status = [ChartStatus("numeric_boxplots", "Numerical boxplots", "failed", "ValueError: x")]
    report = render_report(inspection)
    assert "| Median | Mode | Std |" in report and "| Mode | Zero share |" in report
    assert "Text value summaries" in report and "Most common missing-value patterns" in report
    assert "Chart availability" in report and "ValueError: x" in report


def test_json_report_is_valid_and_has_no_raw_rows():
    import json

    from smart_data_inspector.reporting.json.renderer import render_json_report
    data = json.loads(render_json_report(make_inspection()))
    assert data["overview"]["rows"] == 4 and len(data["columns"]) == 3
    assert "rows" not in data["source"] and data["findings"][0]["check"] == "High missingness"
