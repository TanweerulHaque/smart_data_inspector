"""The one workflow shared by the CLI and the web UI: load, inspect, chart, render, write.

Output (``output`` argument):
* omitted: the current working directory;
* a directory: ``<input-stem>_<run-id>.md`` / ``.json`` and ``<input-stem>_<run-id>_assets/``;
* a path ending in ``.md`` or ``.json``: that report file, with charts in ``<stem>_assets/``.

Everything is staged in a hidden directory first and moved into place together, so a
failed run leaves no partial report or orphaned charts behind.
"""

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .config import InspectionConfig
from .inspector import inspect_dataset
from .loaders import load_dataset
from .models import ChartStatus, Inspection, InspectionError
from .reporting.json.renderer import render_json_report
from .reporting.markdown.renderer import render_report
from .utils.files import commit_staged

FORMATS = {"markdown": ["markdown"], "json": ["json"], "both": ["markdown", "json"]}
SUFFIXES = {"markdown": ".md", "json": ".json"}
RENDERERS = {"markdown": render_report, "json": render_json_report}


@dataclass
class RunResult:
    inspection: Inspection
    reports: dict[str, Path]
    assets_dir: Path | None


def plan_outputs(source: Path, output: str | Path | None, report_format: str | None,
                 run_id: str) -> tuple[dict[str, Path], Path]:
    """Return {format: report path} and the chart directory, without touching disk."""
    if report_format not in (None, *FORMATS):
        raise InspectionError(f"Unknown report format {report_format!r}; use markdown, json or both.")
    target = Path(output).expanduser() if output else Path.cwd()
    implied = {".md": "markdown", ".json": "json"}.get(target.suffix.lower())
    if implied and not target.is_dir():
        formats = FORMATS[report_format or implied]
        if implied not in formats:
            raise InspectionError(f"Output {target.name!r} does not match --format {report_format}.")
        base = target.with_suffix("")
    elif target.is_file() or (target.suffix and not target.exists()):
        raise InspectionError("Output must be a directory or a report path ending in .md or .json.")
    else:
        formats = FORMATS[report_format or "markdown"]
        base = target / f"{source.stem}_{run_id}"
    reports = {kind: base.with_name(base.name + SUFFIXES[kind]) for kind in formats}
    return reports, base.with_name(base.name + "_assets")


def run_inspection(input_path: str | Path | None, output: str | Path | None = None, *,
                   report_format: str | None = None, charts: bool = True,
                   config: InspectionConfig | None = None, flatten_json: bool = False) -> RunResult:
    """Inspect one file and write its report(s); raises InspectionError for bad input or output."""
    if not input_path or not str(input_path).strip():
        raise InspectionError("An input file path is required (CSV, JSON, JSON Lines or Parquet).")
    source = Path(str(input_path).strip()).expanduser()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    reports, assets_dir = plan_outputs(source, output, report_format, run_id)
    if any(path.resolve() == source.resolve() for path in (*reports.values(), assets_dir)):
        raise InspectionError("Output must not overwrite the input file, including links to it.")

    dataset = load_dataset(source, flatten_json=flatten_json)
    inspection = inspect_dataset(dataset, config or InspectionConfig())
    inspection.generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    staging = assets_dir.parent / f".sdi-staging-{run_id}"
    staging.mkdir(parents=True)
    try:
        if charts:
            from .visualizations import generate_charts
            inspection.assets, inspection.chart_status = generate_charts(
                dataset.frame, inspection, staging / "assets", assets_dir.name)
        else:
            inspection.chart_status = [ChartStatus("all", "All charts", "disabled", "charts were turned off")]
        dataset.frame = None  # free the table; only summaries are needed from here
        moves = [(staging / "assets", assets_dir)] if inspection.assets else []
        for kind, destination in reports.items():
            staged = staging / f"report{SUFFIXES[kind]}"
            staged.write_text(RENDERERS[kind](inspection), encoding="utf-8")
            moves.append((staged, destination))
        commit_staged(moves)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return RunResult(inspection, reports, assets_dir if inspection.assets else None)
