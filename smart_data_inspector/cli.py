"""Inspect one local file and write a Markdown report."""

import argparse
from pathlib import Path

from .inspector import DEFAULT_MISSING_VALUES, InspectionConfig, inspect_dataset
from .loaders import InspectionError, load_dataset
from .report import render_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Example: python -m smart_data_inspector data.csv -o reports/data.md",
    )
    parser.add_argument("input", type=Path, help="one UTF-8 .csv or flat .json file")
    parser.add_argument("-o", "--output", type=Path, help="Markdown path; default: <input-stem>.report.md")
    parser.add_argument(
        "--missing-threshold", type=float, default=0.2, metavar="FRACTION",
        help="flag columns whose missing fraction is at least this value, in (0, 1]",
    )
    parser.add_argument(
        "--top-values", type=int, default=3, metavar="N",
        help="maximum frequent values shown per categorical column; positive integer",
    )
    parser.add_argument(
        "--missing-value", action="append", metavar="TOKEN",
        help="repeat to replace default missing tokens (NA, N/A, null, none, nan); blanks remain missing",
    )
    args = parser.parse_args(argv)
    try:
        config = InspectionConfig(
            missing_threshold=args.missing_threshold,
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
        report = render_report(inspect_dataset(dataset, config))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
    except (InspectionError, ValueError, ArithmeticError, RecursionError) as exc:
        parser.error(str(exc))
    except OSError as exc:
        parser.error(f"Cannot write report: {exc.strerror or exc} ({exc.filename!r}).")
    print(output)
    return 0
