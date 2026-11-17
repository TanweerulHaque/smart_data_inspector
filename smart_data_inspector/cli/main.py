"""Inspect one local CSV/JSON file and write an explainable Markdown report."""

import argparse
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text

from ..config import DEFAULT_MISSING_VALUES, InspectionConfig
from ..inspector import inspect_dataset
from ..loaders import InspectionError, load_dataset
from ..report import render_report
from ..utils.files import write_text_atomic


def _add_arguments(parser: argparse.ArgumentParser) -> None:
    defaults = InspectionConfig()
    parser.add_argument("input", type=Path, help="one UTF-8 .csv or flat .json file")
    parser.add_argument("-o", "--output", type=Path, help="Markdown path; default: <input-stem>.report.md")
    parser.add_argument("--missing-threshold", type=float, default=defaults.missing_threshold, metavar="FRACTION",
                        help="high missingness threshold in (0, 1]; default: 0.05 (5%%)")
    parser.add_argument("--iqr-multiplier", type=float, default=defaults.iqr_multiplier,
                        help="positive IQR fence multiplier; default: 1.5")
    parser.add_argument("--top-values", type=int, default=defaults.top_values, metavar="N",
                        help="maximum frequent categorical values; default: 5")
    parser.add_argument("--missing-value", action="append", metavar="TOKEN",
                        help="repeat to replace default missing markers; blanks/nulls remain missing")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect_parser = commands.add_parser("inspect", help="inspect one dataset")
    _add_arguments(inspect_parser)
    args = parser.parse_args(argv)
    console = Console(highlight=False)
    try:
        config = InspectionConfig(
            missing_threshold=args.missing_threshold, iqr_multiplier=args.iqr_multiplier,
            top_values=args.top_values,
            missing_values=tuple(args.missing_value) if args.missing_value is not None else DEFAULT_MISSING_VALUES,
        )
        dataset = load_dataset(args.input)
        output = (args.output or dataset.source.with_suffix(".report.md")).expanduser()
        if output.resolve() == dataset.source.resolve() or (
            output.exists() and output.samefile(dataset.source)
        ):
            raise InspectionError("Output must not overwrite the input file, including links to it.")
        if output.suffix.lower() != ".md":
            raise InspectionError("Output must have a .md extension.")
        if output.is_dir():
            raise InspectionError("Output must be a Markdown file, not a directory.")
        inspection = inspect_dataset(dataset, config)
        report = render_report(inspection)
        write_text_atomic(output, report)
    except (InspectionError, ValueError, ArithmeticError, RecursionError) as exc:
        Console(stderr=True).print(f"Error: {exc}", style="red", markup=False)
        return 2
    except OSError as exc:
        Console(stderr=True).print(f"Cannot write report: {exc.strerror or exc} ({exc.filename!r}).",
                                   style="red", markup=False)
        return 2
    console.print("Smart Data Inspector", style="bold cyan")
    console.print(f"Input: {dataset.source}", markup=False)
    console.print(f"Rows: {len(dataset.rows):,} | Columns: {len(dataset.columns):,} | "
                  f"Additional duplicate rows: {inspection.duplicate_rows:,}", markup=False)
    console.print(f"Missing cells: {sum(column.missing_count for column in inspection.columns):,} | "
                  f"Approximate DataFrame memory: {inspection.memory_bytes:,} bytes", markup=False)
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
    console.print(f"Report: {output}", markup=False)
    return 0
