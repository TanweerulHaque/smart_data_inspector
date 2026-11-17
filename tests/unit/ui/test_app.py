from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).resolve().parents[3] / "smart_data_inspector" / "ui" / "app.py"


def _app(input_path: str, output_dir: Path, charts: bool = True) -> AppTest:
    app = AppTest.from_file(str(APP), default_timeout=120)
    app.run()
    app.text_input(key="input_path").set_value(input_path)
    app.text_input(key="output_dir").set_value(str(output_dir))
    app.checkbox(key="charts").set_value(charts)
    app.button(key="run").click()
    return app.run()


def _csv(tmp_path: Path) -> Path:
    path = tmp_path / "sample.csv"
    rows = ["id,group,value,score,when"]
    rows += [f"{i},{'abc'[i % 3]},{i * 1.5 if i % 7 else ''},{(i * 37) % 11},2024-01-{1 + i % 28:02d}"
             for i in range(40)]
    rows.append(rows[-1])  # one duplicate row
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def test_run_writes_reports_and_shows_results(tmp_path):
    out = tmp_path / "out"
    app = _app(str(_csv(tmp_path)), out)
    assert not app.exception
    assert not app.error
    labels = {metric.label: metric.value for metric in app.metric}
    assert {"Rows", "Columns", "Completeness", "Duplicate rows", "Findings"} <= set(labels)
    assert labels["Rows"] == "41" and labels["Columns"] == "5"
    assert len(list(out.glob("sample_*.md"))) == 1
    assert len(list(out.glob("sample_*.json"))) == 1
    assert [tab.label for tab in app.tabs] == ["Report", "Findings", "Columns", "Charts", "Downloads"]
    assert len(app.dataframe) >= 2
    tabs = {tab.label: [child.type for child in tab.children.values()] for tab in app.tabs}
    pngs = list(next(out.glob("sample_*_assets")).glob("*.png"))
    assert pngs and tabs["Report"].count("image") == len(pngs)  # charts inlined in the report
    assert tabs["Charts"].count("image") == len(pngs)
    assert tabs["Downloads"].count("download_button") == 2
    # Re-running (e.g. a filter change) reuses the stored result instead of inspecting again.
    app.multiselect(key="severity_filter").set_value([]).run()
    assert not app.exception
    assert len(list(out.glob("sample_*.md"))) == 1


def test_run_without_charts(tmp_path):
    app = _app(str(_csv(tmp_path)), tmp_path, charts=False)
    assert not app.exception and not app.error
    assert not list(tmp_path.glob("*_assets"))


def test_empty_path_shows_error(tmp_path):
    app = _app("  ", tmp_path)
    assert not app.exception
    assert "input file path" in app.error[0].value
    assert not list(tmp_path.glob("*.md"))


def test_missing_file_shows_error(tmp_path):
    app = _app(str(tmp_path / "nope.csv"), tmp_path)
    assert not app.exception
    assert len(app.error) == 1
    assert not app.metric
