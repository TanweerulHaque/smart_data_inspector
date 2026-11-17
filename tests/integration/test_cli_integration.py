"""End-to-end tests for the current run-specific narrative workflow."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

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


def test_two_default_runs_have_distinct_report_and_asset_directories(cli, tmp_path):
    source = tmp_path / "input.csv"
    source.write_text("value\n1\n2\n", encoding="utf-8")
    reports_dir = Path(__file__).resolve().parents[2] / "reports"
    before = set(reports_dir.glob("input_*.md"))
    first, second = cli("inspect", source), cli("inspect", source)
    assert first.returncode == second.returncode == 0
    created = set(reports_dir.glob("input_*.md")) - before
    assert len(created) == 2
    for report in created:
        report.unlink()
        shutil.rmtree(reports_dir.parent / "assets" / report.stem)
