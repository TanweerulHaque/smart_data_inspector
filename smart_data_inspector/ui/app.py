"""Minimal Streamlit front end over the shared CLI workflow.

Launch from the repository root with ``streamlit run smart_data_inspector/ui/app.py``.
The page only calls :func:`smart_data_inspector.runner.run_inspection` and then displays
the files that run wrote to disk (Markdown, JSON and chart PNGs); it never profiles data itself.
"""

import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from smart_data_inspector.config import InspectionConfig
from smart_data_inspector.models import InspectionError
from smart_data_inspector.runner import run_inspection

IMAGE_LINE = re.compile(r"^\s*!\[(?P<caption>[^\]]*)\]\(<?(?P<path>[^)>]+)>?\)\s*$")


def load_artifacts(result) -> dict:
    """Read back exactly what the run wrote, so the page shows the committed files."""
    md_path, json_path = result.reports["markdown"], result.reports["json"]
    assets_dir = result.assets_dir
    return {
        "markdown_path": md_path,
        "json_path": json_path,
        "assets_dir": assets_dir,
        "markdown": md_path.read_text(encoding="utf-8"),
        "data": json.loads(json_path.read_text(encoding="utf-8")),
        "images": sorted(assets_dir.glob("*.png")) if assets_dir and assets_dir.is_dir() else [],
    }


def render_markdown_with_images(text: str, base_dir: Path) -> None:
    """st.markdown cannot load local relative images, so swap image lines for st.image."""
    buffer: list[str] = []
    for line in text.splitlines():
        match = IMAGE_LINE.match(line)
        if not match:
            buffer.append(line)
            continue
        if buffer:
            st.markdown("\n".join(buffer))
            buffer = []
        image = (base_dir / match["path"].strip()).resolve()
        if image.is_file():
            st.image(str(image), caption=match["caption"] or None)
        else:
            st.warning(f"Chart file not found: {match['path']}")
    if buffer:
        st.markdown("\n".join(buffer))


def show_metrics(data: dict) -> None:
    overview = data.get("overview") or {}
    completeness = overview.get("completeness")
    cols = st.columns(5)
    cols[0].metric("Rows", f"{overview.get('rows', 0):,}")
    cols[1].metric("Columns", overview.get("columns", 0))
    cols[2].metric("Completeness", "n/a" if completeness is None else f"{completeness:.2%}")
    cols[3].metric("Duplicate rows", overview.get("duplicate_rows", 0))
    cols[4].metric("Findings", overview.get("finding_count", len(data.get("findings") or [])))


def show_findings(data: dict) -> None:
    findings = pd.DataFrame(data.get("findings") or [],
                            columns=["severity", "check", "column", "evidence", "rule"])
    findings["column"] = findings["column"].fillna("(dataset)")
    if findings.empty:
        st.info("No findings were reported.")
        return
    options = sorted(findings["severity"].dropna().unique(), key=lambda level: level != "warning")
    chosen = st.multiselect("Severity", options, default=options, key="severity_filter")
    st.dataframe(findings[findings["severity"].isin(chosen)], hide_index=True)


def show_columns(data: dict) -> None:
    rows = [{
        "name": column.get("name"),
        "inferred_type": column.get("inferred_type"),
        "missing_count": column.get("missing_count"),
        "missing %": None if column.get("missing_fraction") is None
        else round(100 * column["missing_fraction"], 2),
        "distinct": column.get("distinct_count"),
        "likely_identifier": column.get("likely_identifier"),
    } for column in data.get("columns") or []]
    st.dataframe(pd.DataFrame(rows), hide_index=True)


def show_charts(artifacts: dict) -> None:
    data = artifacts["data"]
    charts = data.get("charts") or {}
    captions = {Path(asset.get("relative_path", "")).name: asset.get("caption")
                for asset in charts.get("assets") or [] if isinstance(asset, dict)}
    if artifacts["images"]:
        for image in artifacts["images"]:
            st.image(str(image), caption=captions.get(image.name) or image.name)
    else:
        st.info("No chart images were written for this run.")
    status = pd.DataFrame(charts.get("status") or [], columns=["title", "status", "detail"])
    if not status.empty:
        st.subheader("Chart status")
        st.dataframe(status, hide_index=True)


def show_downloads(artifacts: dict) -> None:
    st.download_button("Download Markdown report", artifacts["markdown"],
                       file_name=artifacts["markdown_path"].name, mime="text/markdown")
    st.download_button("Download JSON report", artifacts["json_path"].read_bytes(),
                       file_name=artifacts["json_path"].name, mime="application/json")


def sidebar_run() -> None:
    with st.sidebar:
        st.header("Inspect a file")
        input_path = st.text_input("Input file path (CSV, JSON, JSON Lines or Parquet)", key="input_path")
        output_dir = st.text_input("Output directory", value=str(Path.cwd()), key="output_dir")
        charts = st.checkbox("Generate charts", value=True, key="charts")
        flatten = st.checkbox("Flatten nested JSON", value=False, key="flatten_json")
        threshold = st.number_input("Missing threshold", min_value=0.0, max_value=1.0, value=0.05,
                                    step=0.01, format="%.2f", key="missing_threshold")
        iqr = st.number_input("IQR multiplier", min_value=0.0, value=1.5, step=0.1, key="iqr_multiplier")
        st.caption("Writes both the Markdown and JSON reports (format=both), as the CLI would.")
        clicked = st.button("Run", type="primary", key="run")
    if not clicked:
        return
    st.session_state.pop("artifacts", None)
    if not input_path.strip():
        st.session_state["error"] = "Please enter an input file path."
        return
    try:
        config = InspectionConfig(missing_threshold=float(threshold), iqr_multiplier=float(iqr))
        with st.spinner("Inspecting..."):
            result = run_inspection(input_path, output_dir.strip() or None, report_format="both",
                                    charts=charts, config=config, flatten_json=flatten)
        st.session_state["artifacts"] = load_artifacts(result)
        st.session_state.pop("error", None)
    except (InspectionError, ValueError, OSError) as exc:
        st.session_state["error"] = str(exc)


def main() -> None:
    st.set_page_config(page_title="Smart Data Inspector", layout="wide")
    st.title("Smart Data Inspector")
    sidebar_run()
    if st.session_state.get("error"):
        st.error(st.session_state["error"])
    artifacts = st.session_state.get("artifacts")
    if not artifacts:
        st.write("Enter a file path in the sidebar and press **Run**.")
        return
    show_metrics(artifacts["data"])
    st.caption("Written files:")
    written = [artifacts["markdown_path"], artifacts["json_path"]]
    st.code("\n".join(str(p) for p in written + ([artifacts["assets_dir"]] if artifacts["assets_dir"] else [])),
            language=None, wrap_lines=True)
    report, findings, columns, charts, downloads = st.tabs(
        ["Report", "Findings", "Columns", "Charts", "Downloads"])
    with report:
        render_markdown_with_images(artifacts["markdown"], artifacts["markdown_path"].parent)
    with findings:
        show_findings(artifacts["data"])
    with columns:
        show_columns(artifacts["data"])
    with charts:
        show_charts(artifacts)
    with downloads:
        show_downloads(artifacts)


if __name__ == "__main__":
    main()
