"""Inspect one local CSV, JSON, JSON Lines or Parquet file and write an explainable Markdown and/or JSON report."""

import argparse

from rich.console import Console
from rich.table import Table
from rich.text import Text

from ..config import DEFAULT_MISSING_VALUES, InspectionConfig
from ..models import InspectionError
from ..runner import run_inspection


def _add_arguments(parser: argparse.ArgumentParser) -> None:
    defaults = InspectionConfig()
    parser.add_argument("input", help="required: path to a .csv, .json, .jsonl/.ndjson or .parquet file")
    parser.add_argument("-o", "--output", default=None, metavar="PATH",
                        help="directory for <input>_<run-id> outputs (default: current directory), "
                             "or an exact report file ending in .md or .json")
    parser.add_argument("-f", "--format", dest="report_format", choices=("markdown", "json", "both"),
                        default=None, help="report format; default: markdown (or implied by an -o file extension)")
    parser.add_argument("--flatten-json", action="store_true",
                        help="flatten nested JSON objects (and a top-level object of records) into dotted columns")
    parser.add_argument("--missing-threshold", type=float, default=defaults.missing_threshold, metavar="FRACTION",
                        help="high missingness threshold in (0, 1]; default: 0.05 (5%%)")
    parser.add_argument("--iqr-multiplier", type=float, default=defaults.iqr_multiplier,
                        help="positive IQR fence multiplier; default: 1.5")
    parser.add_argument("--top-values", type=int, default=defaults.top_values, metavar="N",
                        help="maximum frequent categorical values; default: 5")
    markers = parser.add_mutually_exclusive_group()
    markers.add_argument("--missing-value", action="append", metavar="TOKEN",
                         help="repeat to replace the default (case-sensitive) missing markers "
                              f"{', '.join(repr(item) for item in DEFAULT_MISSING_VALUES if item)}; blanks/nulls stay missing")
    markers.add_argument("--no-missing-markers", action="store_true",
                         help="treat only blanks, JSON null and absent keys as missing")
    parser.add_argument("--no-charts", action="store_true", help="skip optional PNG charts")


def _markers(args: argparse.Namespace) -> tuple[str, ...]:
    if args.no_missing_markers:
        return ("",)
    return tuple(args.missing_value) if args.missing_value is not None else DEFAULT_MISSING_VALUES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    _add_arguments(commands.add_parser("inspect", help="inspect one dataset"))
    args = parser.parse_args(argv)
    console = Console(highlight=False)
    try:
        config = InspectionConfig(
            missing_threshold=args.missing_threshold, iqr_multiplier=args.iqr_multiplier,
            top_values=args.top_values, missing_values=_markers(args),
        )
        result = run_inspection(args.input, args.output, report_format=args.report_format,
                                charts=not args.no_charts, config=config, flatten_json=args.flatten_json)
    except (InspectionError, ValueError, ArithmeticError, RecursionError) as exc:
        Console(stderr=True).print(f"Error: {exc}", style="red", markup=False)
        return 2
    except OSError as exc:
        Console(stderr=True).print(f"Cannot write report: {exc.strerror or exc} ({exc.filename!r}).",
                                   style="red", markup=False)
        return 2
    inspection = result.inspection
    dataset = inspection.dataset
    console.print("Smart Data Inspector", style="bold cyan")
    console.print(f"Input: {dataset.source}", markup=False)
    console.print(f"Rows: {dataset.row_count:,} | Columns: {len(dataset.columns):,} | "
                  f"Additional duplicate rows: {inspection.duplicate_rows:,}", markup=False)
    console.print(f"Missing cells: {sum(column.missing_count for column in inspection.columns):,} | "
                  f"Approximate DataFrame memory: {inspection.memory_bytes:,} bytes", markup=False)
    if inspection.assets:
        console.print(f"Charts: {len(inspection.assets):,} PNG asset(s) in {result.assets_dir}", markup=False)
    failed = [item for item in inspection.chart_status if item.status == "failed"]
    for item in failed:
        console.print(f"Chart unavailable: {item.title} ({item.detail})", style="yellow", markup=False)
    if inspection.findings:
        table = Table(title=f"{len(inspection.findings)} potential quality findings")
        for heading in ("Severity", "Check", "Column", "Evidence"):
            table.add_column(heading)
        for finding in inspection.findings:
            table.add_row(*(Text(value) for value in (
                finding.severity, finding.check_name, finding.column or "(dataset)", finding.evidence,
            )))
        console.print(table)
    else:
        console.print("No issues detected by configured rules; this does not guarantee clean data.")
    for kind, path in result.reports.items():
        console.print(f"Report ({kind}): {path}", markup=False)
    return 0
