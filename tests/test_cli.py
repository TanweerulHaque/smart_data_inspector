"""CLI safety and configuration smoke tests."""

from pathlib import Path

from smart_data_inspector.cli.main import main


def test_explicit_output_and_no_charts_work(tmp_path, capsys):
    source, output = tmp_path / "input.csv", tmp_path / "report.md"
    source.write_text("value\n1\n2\n", encoding="utf-8")
    assert main(["inspect", str(source), "--output", str(output), "--no-charts"]) == 0
    assert output.exists()
    assert "Charts:" not in capsys.readouterr().out


def test_invalid_output_extension_is_rejected_without_writing(tmp_path):
    source, output = tmp_path / "input.csv", tmp_path / "report.txt"
    source.write_text("value\n1\n", encoding="utf-8")
    assert main(["inspect", str(source), "--output", str(output)]) == 2
    assert not output.exists()


def test_input_cannot_be_used_as_report(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text("value\n1\n", encoding="utf-8")
    assert main(["inspect", str(source), "--output", str(source)]) == 2
    assert source.read_text(encoding="utf-8") == "value\n1\n"
