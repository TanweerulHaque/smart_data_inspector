"""Renderer contracts exercised directly with the shared result dataclasses."""

import copy
import re
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from smart_data_inspector.config import InspectionConfig
from smart_data_inspector.models import (
    ColumnSummary,
    Dataset,
    Finding,
    Inspection,
    NumericSummary,
)
from smart_data_inspector.report import render_report
from smart_data_inspector.reporting import render_report as package_render_report
from smart_data_inspector.reporting.markdown import (
    render_report as markdown_render_report,
)
from smart_data_inspector.reporting.markdown.renderer import (
    render_report as implementation,
)


def column(name="label", **overrides):
    base = ColumnSummary(
        name=name, inferred_type="string", missing_count=1, missing_fraction=0.25,
        non_null_count=3, distinct_count=2, type_counts={"string": 3},
        top_values=[("red", 2), ("blue", 1)], numeric=None,
    )
    return replace(base, **overrides)


@pytest.fixture
def inspection():
    numeric = NumericSummary(4, 1.0, 4.0, 2.5, 2.5, 1.2909944487358056, 1.75, 3.25)
    columns = [
        column(),
        column("reading", inferred_type="number", missing_count=0, missing_fraction=0,
               non_null_count=4, distinct_count=4, type_counts={"integer": 4},
               top_values=[(1, 1), (2, 1), (3, 1), (4, 1)], numeric=numeric),
        column("sample_id", inferred_type="integer", missing_count=0, missing_fraction=0,
               non_null_count=4, distinct_count=4, type_counts={"integer": 4},
               top_values=[(101, 1), (102, 1), (103, 1), (104, 1)],
               numeric=replace(numeric, minimum=101, maximum=104, mean=102.5, median=102.5,
                               q1=101.75, q3=103.25), likely_identifier=True),
        column("mixed", inferred_type="mixed", missing_count=0, missing_fraction=0,
               non_null_count=4, distinct_count=4, type_counts={"integer": 3, "string": 1},
               top_values=[(1, 1), ("bad", 1), (3, 1), (4, 1)],
               numeric=NumericSummary(3, 1, 4, 8 / 3, 3, 1.5275252316519465, 2, 3.5),
               unexpected_values=["bad"]),
        column("empty", inferred_type="empty", missing_count=4, missing_fraction=1,
               non_null_count=0, distinct_count=0, type_counts={}, top_values=[]),
    ]
    dataset = Dataset(Path("/input/experiment.CSV"), "CSV", [item.name for item in columns], [
        ["red", 1, 101, 1, None], ["red", 2, 102, "bad", None],
        ["blue", 3, 103, 3, None], [None, 4, 104, 4, None],
    ])
    findings = [
        Finding("High missingness", "empty", "warning", "4/4 values missing", "fraction >= 0.05",
                "Review collection coverage."),
        Finding("Mixed types", "mixed", "info", "Unexpected token: bad", "numeric fraction >= 0.8",
                "Check the original token; categorical codes may be intentional."),
    ]
    return Inspection(dataset, InspectionConfig(), columns, 0, findings, 4096, 2048)


def section(report, heading):
    return report.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]


def table_rows(text):
    return [line for line in text.splitlines() if line.startswith("| ")]


def test_public_facades_export_the_standalone_renderer():
    assert render_report is implementation
    assert package_render_report is implementation
    assert markdown_render_report is implementation


def test_overview_summary_and_section_order(inspection):
    report = render_report(inspection)
    assert report.startswith("# Data Inspection Report\n")
    assert report.endswith("\n")
    headings = re.findall(r"^## (.+)$", report, re.MULTILINE)
    assert headings == ["Overview", "Overall summary", "Schema inventory", "Missing values", "Duplicate rows",
                        "Numeric summaries", "Categorical summaries", "Data quality findings", "Rules and limitations"]
    overview = section(report, "Overview")
    for expected in (
        "| Source file | experiment.CSV |", "| Source path | /input/experiment.CSV |",
        "| Extension | .CSV |", "| Format | CSV |", "| File size | 2,048 bytes (2 KiB) |",
        "| Rows | 4 |", "| Columns | 5 |", "| Estimated in-memory size | 4,096 bytes (4 KiB) |",
    ):
        assert expected in overview
    summary = section(report, "Overall summary")
    assert "Missing cells: 5 across 2 column(s)." in summary
    assert "Potential quality findings: 2." in summary
    assert "info: 1, warning: 1" in summary
    assert "not proof of invalid data or scientific validity" in summary


def test_schema_uses_semantic_and_observed_types_without_fabricated_dtypes(inspection):
    schema = section(render_report(inspection), "Schema inventory")
    assert "observed scalar types show the evidence used for inference" in schema
    assert "| label | 3 | string | string: 3 | No |" in schema
    assert "| reading | 4 | number | integer: 4 | No |" in schema
    assert "| mixed | 4 | mixed | integer: 3, string: 1 | No |" in schema
    assert "| empty | 0 | empty | N/A | No |" in schema
    assert "| sample_id | 4 | integer | integer: 4 | Yes |" in schema
    assert "float64" not in schema


def test_missing_table_includes_zero_and_fully_missing_columns(inspection):
    missing = section(render_report(inspection), "Missing values")
    assert "at least 5% missing" in missing
    assert "| label | 1 | 25% | 3 | Yes |" in missing
    assert "| reading | 0 | 0% | 4 | No |" in missing
    assert "| empty | 4 | 100% | 0 | Yes |" in missing
    assert len(table_rows(missing)) == len(inspection.columns) + 2


def test_duplicate_count_is_additional_occurrences_not_group_members(inspection):
    inspection.duplicate_rows = 2
    duplicates = section(render_report(inspection), "Duplicate rows")
    assert "| Additional duplicate rows | 2 |" in duplicates
    assert "| Share of all rows | 50% |" in duplicates
    assert "three identical rows contribute two additional rows" in duplicates
    assert "after missing-value normalization" in duplicates
    assert "not the number of all rows belonging to duplicate groups" in duplicates


def test_numeric_summary_has_all_statistics_and_explicit_subset_notes(inspection):
    numeric = section(render_report(inspection), "Numeric summaries")
    assert "sample standard deviation (ddof=1)" in numeric
    assert "six significant digits" in numeric
    assert "Quartiles use linear interpolation" in numeric
    assert "| reading | 4 | 0 | 1 | 4 | 2.5 | 2.5 | 1.29099 | 1.75 | 3.25 | Finite numeric values |" in numeric
    assert "| mixed | 3 | 0 | 1 | 4 | 2.66667 | 3 | 1.52753 | 2 | 3.5 | Numeric subset only; not the full column |" in numeric
    assert "Likely identifier; magnitudes may not be meaningful" in numeric


def test_categorical_modes_frequencies_and_numeric_identifiers(inspection):
    categorical = section(render_report(inspection), "Categorical summaries")
    assert '| label | 2 | "red" | 2 / 3 (66.6667%) | "red" (2); "blue" (1) |  |' in categorical
    assert "| sample_id | 4 | N/A | N/A | N/A | Likely identifier; mode and top values suppressed |" in categorical
    assert "101" not in categorical
    assert "| reading |" not in categorical
    assert "first-seen order" in categorical
    assert "need not be a unique mode" in categorical
    assert "Up to 5" in categorical


def test_string_identifiers_do_not_display_misleading_modes(inspection):
    inspection.columns[0].likely_identifier = True
    categorical = section(render_report(inspection), "Categorical summaries")
    assert "| label | 2 | N/A | N/A | N/A | Likely identifier; mode and top values suppressed |" in categorical
    assert '"red"' not in categorical


def test_top_values_limit_and_rules_are_read_from_config(inspection):
    inspection.config = InspectionConfig(
        missing_threshold=0.5, top_values=1, missing_values=("MISSING",), iqr_multiplier=3,
        mixed_numeric_threshold=0.9, identifier_unique_ratio=1, identifier_min_count=20, outlier_min_count=8,
    )
    report = render_report(inspection)
    categorical = section(report, "Categorical summaries")
    assert "Up to 1 most frequent" in categorical
    assert '"red" (2)' in categorical
    assert '"blue" (1)' not in categorical
    assert "| label | 1 | 25% | 3 | No |" in section(report, "Missing values")
    rules = section(report, "Rules and limitations")
    for expected in ('"MISSING"', "missing fraction >= 50%", "at least 90% numeric", "at least 100% uniqueness",
                     "at least 20 values", "Q1 - 3 × IQR", "Q3 + 3 × IQR", "fewer than 8 finite values"):
        assert expected in rules
    assert '"na"' not in rules


def test_findings_preserve_all_six_structured_fields(inspection):
    inspection.findings.append(Finding("Duplicates", None, "info", "2 additional rows", "full-row match", "Review replicates."))
    findings = section(render_report(inspection), "Data quality findings")
    assert "| Check name | Column | Severity | Evidence | Rule | Explanation |" in findings
    assert "| High missingness | empty | warning | 4/4 values missing | fraction &gt;= 0.05 | Review collection coverage. |" in findings
    assert "| Duplicates | (whole dataset) | info | 2 additional rows | full-row match | Review replicates. |" in findings


def test_no_findings_does_not_claim_clean_or_scientifically_valid_data(inspection):
    inspection.findings.clear()
    report = render_report(inspection)
    for heading in ("Overall summary", "Data quality findings"):
        assert "No potential issues detected by the configured rules. This does not guarantee clean data." in section(report, heading)
    assert "No additional duplicate rows were detected under this comparison rule." in report
    assert "No findings does not prove the data are clean" in report


def test_default_rule_limitations_are_comprehensive(inspection):
    rules = section(render_report(inspection), "Rules and limitations")
    for expected in (
        "missing fraction >= 5%", "at least 80% numeric", "Q1 - 1.5 × IQR", "Q3 + 1.5 × IQR",
        "zero IQR or fewer than 4 finite values", "Pandas/NumPy floating-point", "round large integers",
        "JSON preserves native types", "quoted numbers and booleans remain strings", "no domain schema",
        "No nested JSON, JSON Lines, date inference, plots or domain validation", "in memory, not streamed",
        "nonfinite values are flagged", "excluded from numeric statistics and outlier fences",
        "not establish scientific validity", "source file is never modified", '"nan"',
    ):
        assert expected in rules


@pytest.mark.parametrize("invalid", [None, float("nan"), float("inf"), -float("inf"),
                                     Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity")])
def test_undefined_and_nonfinite_statistics_are_na_without_crashing(inspection, invalid):
    inspection.columns[1].numeric = NumericSummary(0, invalid, invalid, invalid, invalid, invalid, invalid, invalid, 2)
    numeric = section(render_report(inspection), "Numeric summaries")
    assert "| reading | 0 | 2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Finite numeric values |" in numeric


def test_single_finite_value_has_na_sample_standard_deviation(inspection):
    inspection.columns[1].numeric = NumericSummary(1, 1, 1, 1, 1, None, 1, 1)
    numeric = section(render_report(inspection), "Numeric summaries")
    assert "| reading | 1 | 0 | 1 | 1 | 1 | 1 | N/A | 1 | 1 |" in numeric


def test_tiny_and_huge_statistics_use_six_significant_digits(inspection):
    inspection.columns[1].numeric = NumericSummary(
        4, -1.23456789e300, 1.23456789e300, 1.23456789e-100, 1.23456789123,
        1e300, 1e-100, 1e100,
    )
    numeric = section(render_report(inspection), "Numeric summaries")
    assert "| reading | 4 | 0 | -1.23457e+300 | 1.23457e+300 | 1.23457e-100 | 1.23457 | 1e+300 | 1e-100 | 1e+100 |" in numeric


def test_categorical_values_distinguish_strings_booleans_and_nonfinite_numbers(inspection):
    inspection.columns = [column(
        "special", inferred_type="mixed", missing_count=0, missing_fraction=0, non_null_count=10,
        distinct_count=10, top_values=[("1", 1), (1, 1), (True, 1), (False, 1),
                                     (float("inf"), 1), (-float("inf"), 1), (float("nan"), 1),
                                     (Decimal("Infinity"), 1), (Decimal("1.23456789"), 1),
                                     (Decimal("1e10000"), 1)],
    )]
    inspection.config = InspectionConfig(top_values=10)
    categorical = section(render_report(inspection), "Categorical summaries")
    assert '"1" (1); 1 (1); true (1); false (1); +Infinity (1); -Infinity (1); NaN (1); +Infinity (1); 1.23457 (1); 1e+10000 (1)' in categorical


def test_empty_categorical_frequencies_are_na_not_none_or_division_by_zero(inspection):
    inspection.columns = [column(non_null_count=0, top_values=[], distinct_count=0)]
    categorical = section(render_report(inspection), "Categorical summaries")
    assert "| label | 0 | N/A | N/A | N/A |  |" in categorical


def test_empty_dataset_and_unavailable_file_metadata(inspection):
    inspection.dataset = Dataset(Path("/not/read/empty"), "JSON", [], [])
    inspection.columns = []
    inspection.findings = []
    inspection.file_size_bytes = None
    inspection.memory_bytes = 0
    report = render_report(inspection)
    overview = section(report, "Overview")
    assert "| Extension | N/A |" in overview
    assert "| File size | N/A |" in overview
    assert "| Estimated in-memory size | 0 bytes |" in overview
    assert "| Rows | 0 |" in overview
    assert "| Columns | 0 |" in overview
    assert "| Share of all rows | N/A |" in section(report, "Duplicate rows")
    assert "No numeric values to summarize." in report
    assert "No categorical values to summarize." in report


def test_missing_fraction_for_zero_rows_is_undefined(inspection):
    inspection.dataset.rows.clear()
    inspection.columns = [column(missing_count=0, missing_fraction=0, non_null_count=0, top_values=[])]
    assert "| label | 0 | N/A | 0 | No |" in section(render_report(inspection), "Missing values")


def test_renderer_does_not_read_source_or_recompute_frame_or_mutate_result(inspection, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Renderer attempted I/O or DataFrame reconstruction")

    before = copy.deepcopy(inspection)
    monkeypatch.setattr(Path, "stat", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Dataset, "to_frame", forbidden)
    first = render_report(inspection)
    assert first == render_report(inspection)
    assert inspection == before


def test_escaping_untrusted_names_values_rules_and_all_finding_fields(inspection):
    payload = 'bad|*bold* _em_ [link](https://evil.invalid) ![img](x) <script>& `code` \\ path\n## injected\r\t\u2028\u2029'
    escaped = ('bad\\|\\*bold\\* \\_em\\_ \\[link\\](https://evil.invalid) !\\[img\\](x) '
               '&lt;script&gt;&amp; \\`code\\` \\\\ path\\n## injected\\r\\t\\u2028\\u2029')
    inspection.dataset.source = Path("/input") / (payload + ".csv")
    inspection.dataset.format = payload
    inspection.columns[0] = column(payload, top_values=[(payload, 3)], inferred_type=payload,
                                   type_counts={payload: 3})
    inspection.findings = [Finding(payload, payload, payload, payload, payload, payload)]
    inspection.config = InspectionConfig(missing_values=(payload,))
    report = render_report(inspection)
    assert escaped in report
    assert "<script>" not in report
    assert "[link](" not in report
    assert "\n## injected" not in report
    assert "\r" not in report
    assert "\t" not in report
    assert "\u2028" not in report
    assert "\u2029" not in report
    findings = section(report, "Data quality findings")
    finding_row = table_rows(findings)[2]
    assert finding_row == "| " + " | ".join([escaped] * 6) + " |"
    # A literal backslash before a pipe must not defeat Markdown table escaping.
    inspection.columns[0] = column("back\\|slash", top_values=[("<b>|[x](y)\nline", 3)])
    categorical = section(render_report(inspection), "Categorical summaries")
    assert r"back\\\|slash" in categorical
    assert "&lt;b&gt;\\|\\[x\\](y)" in categorical


def test_intraword_underscores_remain_readable_but_markup_is_escaped(inspection):
    inspection.columns = [column("ordinary_column_name _emphasis_ **strong** ~~strike~~")]
    schema = section(render_report(inspection), "Schema inventory")
    assert r"ordinary_column_name \_emphasis\_ \*\*strong\*\* \~\~strike\~\~" in schema
