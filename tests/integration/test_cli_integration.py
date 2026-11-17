"""Exercise the installed interpreter's real module entry point, not a mocked main."""

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def cli():
    def run(*arguments):
        return subprocess.run(
            [sys.executable, "-m", "smart_data_inspector", *map(str, arguments)],
            cwd=PROJECT_ROOT,
            env={**os.environ, "NO_COLOR": "1", "COLUMNS": "240"},
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=15,
        )
    return run


def write_dataset(root, suffix, records):
    path = root / ("input." + suffix)
    if suffix == "json":
        path.write_text(json.dumps(records), encoding="utf-8")
    else:
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    return path


def section(report, heading):
    return report.split(heading + "\n", 1)[1].split("\n## ", 1)[0]


def table_rows(report, heading):
    # Integration fixtures contain no escaped pipes; omit header and separator.
    lines = [line for line in section(report, heading).splitlines() if line.startswith("| ")]
    return [[cell.strip() for cell in line.strip("|").split("|")] for line in lines[2:]]


def read_successful_report(result, output):
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert output.is_file()
    compact = "".join(result.stdout.split())
    assert "Report:" + "".join(str(output).split()) in compact
    return output.read_text(encoding="utf-8")


@pytest.mark.parametrize("suffix", ["csv", "json"])
def test_end_to_end_report_and_rich_metrics_in_both_formats(cli, tmp_path, suffix):
    records = [{"measurement": v, "label": label} for v, label in
               [(1, "alpha"), (2, "alpha"), (3, "beta"), (4, "beta"),
                (100, "gamma"), (1, "alpha"), (None, "gamma")]]
    source = write_dataset(tmp_path, suffix, records)
    original = source.read_bytes()
    result = cli("inspect", source)
    report = read_successful_report(result, source.with_suffix(".report.md"))
    assert "Smart Data Inspector" in result.stdout
    assert "Rows: 7 | Columns: 2 | Additional duplicate rows: 1" in result.stdout
    assert "Missing cells: 1 | Approximate DataFrame memory:" in result.stdout
    assert "potential quality findings" in result.stdout
    overview = dict(table_rows(report, "## Overview"))
    assert overview["Format"] == suffix.upper()
    assert (overview["Rows"], overview["Columns"]) == ("7", "2")
    assert "bytes" in overview["File size"]
    assert "bytes" in overview["Estimated in-memory size"]
    numeric, = table_rows(report, "## Numeric summaries")
    assert numeric[:7] == ["measurement", "6", "0", "1", "100", "18.5", "2.5"]
    assert numeric[8:10] == ["1.25", "3.75"]
    findings = table_rows(report, "## Data quality findings")
    assert {(row[0], row[1]) for row in findings} == {
        ("Duplicate rows", "(whole dataset)"),
        ("High missingness", "measurement"),
        ("Potential numerical outliers", "measurement"),
    }
    assert source.read_bytes() == original


@pytest.mark.parametrize("suffix", ["csv", "json"])
def test_default_five_percent_missing_threshold_and_five_top_values(cli, tmp_path, suffix):
    records = [{"measurement": i if i else None, "label": "ABCDEF"[i % 6]} for i in range(20)]
    source = write_dataset(tmp_path, suffix, records)
    output = tmp_path / "default.md"
    report = read_successful_report(cli("inspect", source, "-o", output), output)
    missing = table_rows(report, "## Missing values")
    assert missing[0] == ["measurement", "1", "5%", "19", "Yes"]
    findings = table_rows(report, "## Data quality findings")
    assert any(row[:3] == ["High missingness", "measurement", "warning"] for row in findings)
    categories, = [row for row in table_rows(report, "## Categorical summaries") if row[0] == "label"]
    for value in "ABCDE":
        assert f'"{value}"' in categories[4]
    assert '"F"' not in categories[4]
    changed = tmp_path / "raised-threshold.md"
    report = read_successful_report(
        cli("inspect", source, "-o", changed, "--missing-threshold", "0.050001"), changed,
    )
    findings = table_rows(report, "## Data quality findings")
    assert any(row[:3] == ["Missing values", "measurement", "info"] for row in findings)
    assert not any(row[0] == "High missingness" for row in findings)


@pytest.mark.parametrize("suffix", ["csv", "json"])
@pytest.mark.parametrize("multiplier, has_outlier", [("1.5", True), ("3", False)])
def test_iqr_multiplier_is_wired_through_to_the_check(cli, tmp_path, suffix, multiplier, has_outlier):
    source = write_dataset(tmp_path, suffix, [{"measurement": v} for v in (1, 2, 3, 4, 10)])
    output = tmp_path / "iqr.md"
    result = cli("inspect", source, "-o", output, "--iqr-multiplier", multiplier)
    report = read_successful_report(result, output)
    findings = table_rows(report, "## Data quality findings")
    assert any(row[0] == "Potential numerical outliers" for row in findings) == has_outlier
    assert f"Q1 - {multiplier} × IQR" in section(report, "## Rules and limitations")
    if has_outlier:
        assert "Examples: 10." in findings[0][3]
    else:
        assert "No issues detected by configured rules" in result.stdout


@pytest.mark.parametrize("suffix", ["csv", "json"])
def test_single_numeric_row_has_undefined_sample_std_and_no_outliers(cli, tmp_path, suffix):
    source = write_dataset(tmp_path, suffix, [{"measurement": 7}])
    result = cli("inspect", source)
    report = read_successful_report(result, source.with_suffix(".report.md"))
    numeric, = table_rows(report, "## Numeric summaries")
    assert numeric[:10] == ["measurement", "1", "0", "7", "7", "7", "7", "N/A", "7", "7"]
    assert "Rows: 1 | Columns: 1 | Additional duplicate rows: 0" in result.stdout
    assert "No issues detected by configured rules" in result.stdout
    assert table_rows(report, "## Data quality findings") == []


@pytest.mark.parametrize("suffix", ["csv", "json"])
def test_all_null_column_is_empty_not_numeric_and_still_reports_quality(cli, tmp_path, suffix):
    source = write_dataset(tmp_path, suffix, [{"measurement": None}, {"measurement": None}])
    result = cli("inspect", source)
    report = read_successful_report(result, source.with_suffix(".report.md"))
    schema, = table_rows(report, "## Schema inventory")
    assert schema == ["measurement", "0", "empty", "N/A", "No"]
    assert table_rows(report, "## Missing values") == [["measurement", "2", "100%", "0", "Yes"]]
    assert "No numeric values to summarize." in section(report, "## Numeric summaries")
    assert "Additional duplicate rows: 1" in result.stdout
    assert "Missing cells: 2" in result.stdout
    assert {row[0] for row in table_rows(report, "## Data quality findings")} == {
        "Duplicate rows", "High missingness",
    }


@pytest.mark.parametrize(
    "name, text, expected",
    [("nested-object.json", '[{"v":{"inner":1}}]', ("nested value", "row 1", "v")),
     ("nested-array.json", '[{"v":[1,2]}]', ("nested value", "row 1", "v")),
     ("lines.json", '{"v":1}\n{"v":2}\n', ("Invalid JSON", "line 2", "column 1", "JSON Lines")),
     ("lines.jsonl", '{"v":1}\n', ("Unsupported file extension", "JSON Lines")),
     ("malformed.json", '[{"v":1},]', ("Invalid JSON", "line 1", "column")),
     ("mapping.json", '{"v":1}', ("top-level array", "flat objects"))],
)
@pytest.mark.parametrize("existing_report", [False, True])
def test_unsupported_json_shapes_and_malformed_errors_are_actionable_and_safe(
    cli, tmp_path, name, text, expected, existing_report,
):
    source = tmp_path / name
    source.write_text(text, encoding="utf-8")
    output = tmp_path / "report.md"
    if existing_report:
        output.write_text("keep this report", encoding="utf-8")
    result = cli("inspect", source, "-o", output)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "Traceback" not in result.stderr
    for message in expected:
        assert message in result.stderr
    if existing_report:
        assert output.read_text(encoding="utf-8") == "keep this report"
    else:
        assert not output.exists()
    assert source.read_text(encoding="utf-8") == text
    assert not source.with_suffix(".report.md").exists()


@pytest.mark.parametrize("arguments", [("--help",), ("inspect", "--help")])
def test_help_succeeds_without_input_or_report_creation(cli, tmp_path, arguments):
    result = cli(*arguments)
    assert result.returncode == 0
    assert result.stderr == ""
    assert "usage:" in result.stdout
    assert "inspect" in result.stdout
    if arguments[0] == "inspect":
        help_text = " ".join(result.stdout.split())
        assert "--missing-threshold" in help_text
        assert "default: 0.05 (5%)" in help_text
        assert "--iqr-multiplier" in help_text
        assert "default: 1.5" in help_text
        assert "--top-values" in help_text
        assert "default: 5" in help_text
    assert list(tmp_path.iterdir()) == []


def test_legacy_path_only_invocation_is_rejected_without_touching_files(cli, tmp_path):
    source = write_dataset(tmp_path, "csv", [{"v": 1}])
    original = source.read_bytes()
    result = cli(source)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "invalid choice" in result.stderr
    assert "inspect" in result.stderr
    assert "Traceback" not in result.stderr
    assert not source.with_suffix(".report.md").exists()
    assert source.read_bytes() == original
