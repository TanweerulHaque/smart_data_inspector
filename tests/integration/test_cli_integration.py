"""End-to-end tests for the current run-specific narrative workflow."""

import json
import subprocess
import sys

import pytest


@pytest.fixture
def cli():
    def run(*arguments):
        return subprocess.run([sys.executable, "-m", "smart_data_inspector", *map(str, arguments)], text=True, capture_output=True)
    return run


@pytest.mark.parametrize("suffix, contents", [
    ("csv", "id,measurement,label\nA,1,control\nB,2,control\nC,100,test\nD,,test\n"),
    ("json", json.dumps([{"id": "A", "measurement": 1, "label": "control"}, {"id": "B", "measurement": 2, "label": "control"}, {"id": "C", "measurement": 100, "label": "test"}, {"id": "D", "label": "test"}])),
])
def test_csv_and_flat_json_create_narrative_report_and_pngs(cli, tmp_path, suffix, contents):
    source = tmp_path / f"input.{suffix}"
    source.write_text(contents, encoding="utf-8")
    report = tmp_path / f"{suffix}.md"
    result = cli("inspect", source, "--output", report)
    assert result.returncode == 0, result.stderr
    text = report.read_text(encoding="utf-8")
    assert "## Overview" in text and "## Data quality findings" in text
    assert "Chapter 7: Recommended next investigations" in text
    assert "![" in text
    assert "Charts:" in result.stdout


def test_nested_json_is_a_clear_unsupported_format_and_creates_no_report(cli, tmp_path):
    source, report = tmp_path / "nested.json", tmp_path / "bad.md"
    source.write_text('{"nested": {"x": 1}}', encoding="utf-8")
    result = cli("inspect", source, "--output", report)
    assert result.returncode == 2
    assert "top-level array" in result.stderr
    assert not report.exists()


def test_default_output_is_the_current_directory_and_runs_never_collide(cli, tmp_path):
    source = tmp_path / "data" / "input.csv"
    source.parent.mkdir()
    source.write_text("value\n1\n2\n", encoding="utf-8")
    first, second = cli("inspect", source), cli("inspect", source)  # cwd is tmp_path (conftest)
    assert first.returncode == second.returncode == 0, first.stderr + second.stderr
    reports = sorted(tmp_path.glob("input_*.md"))
    assert len(reports) == 2
    for report in reports:
        assets = report.with_name(report.stem + "_assets")
        assert assets.is_dir() and any(assets.glob("*.png"))
        assert f"]({assets.name}/" in report.read_text(encoding="utf-8")
    assert not list(tmp_path.glob(".sdi-*"))


def test_json_format_writes_machine_readable_report(cli, tmp_path):
    source = tmp_path / "input.csv"
    source.write_text("value,label\n1,a\n2,b\n2,b\n", encoding="utf-8")
    result = cli("inspect", source, "--format", "json", "--no-charts", "-o", tmp_path / "out")
    assert result.returncode == 0, result.stderr
    (report,) = (tmp_path / "out").glob("input_*.json")
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["overview"]["rows"] == 3 and data["overview"]["duplicate_rows"] == 1
    assert {item["check"] for item in data["findings"]} >= {"Duplicate rows"}
    assert data["charts"]["status"][0]["status"] == "disabled"
    assert not list((tmp_path / "out").glob("*.md"))
