"""Output planning and failure-safe writing in the shared workflow."""

import json

import pytest

from smart_data_inspector import runner
from smart_data_inspector.models import InspectionError
from smart_data_inspector.runner import plan_outputs, run_inspection


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "data.v2.csv"
    path.write_text("x,label\n1,a\n2,\n3,b\n40,a\n", encoding="utf-8")
    return path


def test_directory_output_keeps_dotted_input_stems(tmp_path, source):
    reports, assets = plan_outputs(source, tmp_path / "out", "both", "RUN")
    assert reports == {"markdown": tmp_path / "out/data.v2_RUN.md", "json": tmp_path / "out/data.v2_RUN.json"}
    assert assets == tmp_path / "out/data.v2_RUN_assets"


def test_report_file_output_and_format_conflicts(tmp_path, source):
    reports, assets = plan_outputs(source, tmp_path / "r.md", "both", "RUN")
    assert reports == {"markdown": tmp_path / "r.md", "json": tmp_path / "r.json"}
    assert assets == tmp_path / "r_assets"
    with pytest.raises(InspectionError, match="does not match"):
        plan_outputs(source, tmp_path / "r.md", "json", "RUN")
    with pytest.raises(InspectionError, match="directory or a report path"):
        plan_outputs(source, tmp_path / "r.txt", None, "RUN")


def test_input_path_is_required_and_never_overwritten(tmp_path):
    with pytest.raises(InspectionError, match="required"):
        run_inspection("  ")
    data = tmp_path / "data.json"
    data.write_text('[{"a":1}]')
    with pytest.raises(InspectionError, match="overwrite the input"):
        run_inspection(data, data)
    assert data.read_text() == '[{"a":1}]'


def test_run_writes_reports_and_charts_to_the_current_directory(tmp_path, source):
    result = run_inspection(source, report_format="both")
    assert all(path.parent == tmp_path and path.exists() for path in result.reports.values())
    assert result.assets_dir.is_dir() and result.inspection.dataset.frame is None
    data = json.loads(result.reports["json"].read_text(encoding="utf-8"))
    assert data["overview"]["rows"] == 4


def test_failed_rendering_leaves_nothing_behind_and_keeps_old_report(tmp_path, source, monkeypatch):
    old = tmp_path / "r.md"
    old.write_text("old report")
    monkeypatch.setitem(runner.RENDERERS, "json", lambda inspection: 1 / 0)
    with pytest.raises(ZeroDivisionError):
        run_inspection(source, tmp_path / "r.md", report_format="both")
    assert old.read_text() == "old report"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["data.v2.csv", "r.md"]


def test_chart_failures_and_disabled_charts_are_recorded(tmp_path, source, monkeypatch):
    from smart_data_inspector.visualizations import pipeline

    def broken(*args):
        raise RuntimeError("no fonts")

    monkeypatch.setattr(pipeline, "plot_missingness", broken)
    result = run_inspection(source, tmp_path / "r.md")
    status = {item.key: item for item in result.inspection.chart_status}
    assert status["missingness"].status == "failed" and "no fonts" in status["missingness"].detail
    report = result.reports["markdown"].read_text(encoding="utf-8")
    assert "Chart availability" in report and "RuntimeError: no fonts" in report
    disabled = run_inspection(source, tmp_path / "plain.md", charts=False)
    assert disabled.assets_dir is None
    assert [item.status for item in disabled.inspection.chart_status] == ["disabled"]
