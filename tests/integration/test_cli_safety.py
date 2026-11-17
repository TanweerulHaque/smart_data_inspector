"""User-controlled values must not crash terminal output or damage existing reports."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_cli(*arguments):
    return subprocess.run([sys.executable, "-m", "smart_data_inspector", "inspect", *map(str, arguments)],
                          cwd=PROJECT_ROOT, env={**os.environ, "NO_COLOR": "1", "COLUMNS": "240"},
                          capture_output=True, check=False, text=True, encoding="utf-8", timeout=15)


@pytest.mark.parametrize("suffix,text", [
    ("csv", "[/bad]\nNA\n"),
    ("json", '[{"x":1},{"x":"[/bad]"}]'),
    ("json", '[{"[link=https://example.invalid]":null}]'),
])
def test_rich_markup_in_columns_and_findings_is_plain_text(tmp_path, suffix, text):
    source = tmp_path / f"input.{suffix}"
    source.write_text(text)
    output = tmp_path / "report.md"
    result = run_cli(source, "-o", output)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "Traceback" not in result.stdout
    assert output.exists()
    assert "Report:" in result.stdout


@pytest.mark.parametrize("text", ['[{"x":"\\ud800"}]', '[{"\\ud800":1}]'])
def test_invalid_unicode_in_json_preserves_existing_report(tmp_path, text):
    source = tmp_path / "input.json"
    source.write_text(text)
    output = tmp_path / "report.md"
    output.write_text("keep this report")
    result = run_cli(source, "-o", output)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "Unicode scalar" in result.stderr
    assert "Traceback" not in result.stderr
    assert output.read_text() == "keep this report"


def test_huge_native_integer_json_uses_exclusion_policy_not_cli_error(tmp_path):
    source = tmp_path / "input.json"
    source.write_text('[{"v":' + str(10**309) + '},{"v":1}]')
    output = tmp_path / "report.md"
    result = run_cli(source, "-o", output, "--no-charts")
    assert result.returncode == 0, result.stderr
    assert "Non-finite numeric values" in result.stdout
    report = output.read_text()
    assert "Nonfinite excluded" in report
