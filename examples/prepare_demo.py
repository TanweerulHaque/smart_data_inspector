
"""Flatten provided structures and inject deterministic data-quality issues."""

import argparse
import json
import math
from itertools import islice
from pathlib import Path


def positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("limit must be a positive integer") from None
    if value <= 0:
        raise argparse.ArgumentTypeError("limit must be a positive integer")
    return value


def flatten(material_id: str, structure: dict) -> dict:
    if not isinstance(structure, dict):
        raise TypeError(f"{material_id}: structure must be an object")
    lattice = structure.get("lattice")
    sites = structure.get("sites")
    if not isinstance(lattice, dict) or not isinstance(sites, list):
        raise TypeError(f"{material_id}: expected a lattice object and sites array")

    row: dict[str, str | int | float] = {"material_id": material_id}
    for field, value in (
        ("charge", structure.get("charge")),
        ("lattice_a", lattice.get("a")),
        ("lattice_b", lattice.get("b")),
        ("lattice_c", lattice.get("c")),
        ("volume", lattice.get("volume")),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or (isinstance(value, float) and not math.isfinite(value))
        ):
            raise ValueError(f"{material_id}: {field} must be a finite number")
        row[field] = value

    elements = set()
    for index, site in enumerate(sites):
        species = site.get("species") if isinstance(site, dict) else None
        if not isinstance(species, list) or not species:
            raise ValueError(f"{material_id}: site {index} needs a nonempty species array")
        for specie in species:
            element = specie.get("element") if isinstance(specie, dict) else None
            if not isinstance(element, str) or not element.strip():
                raise ValueError(f"{material_id}: site {index} needs element strings")
            elements.add(element)
    row["site_count"] = len(sites)
    row["elements"] = ", ".join(sorted(elements))
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="JSON object mapping IDs to structures")
    parser.add_argument(
        "--output", type=Path, default=Path("examples/structures_with_issues.json"),
        help="destination JSON array (default: %(default)s)",
    )
    parser.add_argument(
        "--limit", type=positive_int, default=20,
        help="maximum number of source structures (default: %(default)s)",
    )
    args = parser.parse_args()

    try:
        if args.output.resolve() == args.source.resolve() or (
            args.output.exists() and args.output.samefile(args.source)
        ):
            raise ValueError("output must not overwrite the source file")
        data = json.loads(args.source.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not data:
            raise ValueError("source must be a nonempty JSON object mapping IDs to structures")
        rows = [flatten(key, value) for key, value in islice(data.items(), args.limit)]

        # Alternate omitted/null volumes in the first ceil(n / 4) selected rows.
        missing_count = (len(rows) + 3) // 4
        for index in range(missing_count):
            if index % 2 == 0:
                del rows[index]["volume"]
            else:
                rows[index]["volume"] = None
        if missing_count < len(rows):
            rows[missing_count]["volume"] = "not measured"
        rows.append(rows[-1].copy())

        args.output.write_text(
            json.dumps(rows, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        parser.error(str(exc))
    print(f"Wrote {len(rows)} rows (including one appended duplicate) to {args.output}")


if __name__ == "__main__":
    main()
