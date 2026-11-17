"""Convert a CSV file to Parquet with pandas' type inference.

Usage: python scripts/convert_csv_to_parquet.py INPUT.csv [-o OUTPUT.parquet]
The output defaults to INPUT's stem with a .parquet suffix, beside the input.
"""

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", type=Path, help="CSV file to convert")
    parser.add_argument("-o", "--output", type=Path, help="Parquet file to write")
    args = parser.parse_args()
    output = args.output or args.input.with_suffix(".parquet")
    if output.resolve() == args.input.resolve():
        parser.error("output would overwrite the input file")
    # round_trip parsing keeps floats exact; pandas' default fast parser can be off by one ulp.
    pd.read_csv(args.input, float_precision="round_trip").to_parquet(output, index=False)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
