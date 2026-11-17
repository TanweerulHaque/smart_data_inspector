"""Flatten supplied structures into clean and deliberately flawed JSON demo data."""

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
    """Extract eleven scalar features without requiring pymatgen or charge."""
    if not isinstance(material_id, str) or not material_id.strip():
        raise ValueError("material_id must be a nonempty string")
    if not isinstance(structure, dict):
        raise TypeError(f"{material_id}: structure must be an object")
    lattice = structure.get("lattice")
    sites = structure.get("sites")
    if not isinstance(lattice, dict) or not isinstance(sites, list):
        raise TypeError(f"{material_id}: expected a lattice object and sites array")

    row: dict[str, str | int | float] = {"material_id": material_id}
    for field in ("a", "b", "c", "alpha", "beta", "gamma", "volume"):
        value = lattice.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or (isinstance(value, float) and not math.isfinite(value))
        ):
            raise ValueError(f"{material_id}: lattice_{field} must be a finite number")
        row[f"lattice_{field}"] = value

    elements = set()
    for index, site in enumerate(sites):
        species = site.get("species") if isinstance(site, dict) else None
        if not isinstance(species, list) or not species:
            raise ValueError(f"{material_id}: site {index} needs a nonempty species array")
        for specie in species:
            element = specie.get("element") if isinstance(specie, dict) else None
            if not isinstance(element, str) or not element.strip():
                raise ValueError(f"{material_id}: site {index} needs element strings")
            elements.add(element.strip())
    row["num_sites"] = len(sites)
    row["num_distinct_elements"] = len(elements)
    row["elements"] = ", ".join(sorted(elements))
    return row


def introduce_issues(clean_rows: list[dict]) -> list[dict]:
    """Copy flat rows, inject deterministic defects, then duplicate the last row."""
    if not clean_rows:
        raise ValueError("at least one clean row is required to introduce issues")
    rows = [row.copy() for row in clean_rows]
    missing_count = (len(rows) + 3) // 4
    for index in range(missing_count):
        if index % 2 == 0:
            del rows[index]["lattice_volume"]
        else:
            rows[index]["lattice_volume"] = None
    if missing_count < len(rows):
        rows[missing_count]["lattice_volume"] = "not measured"

    extreme = rows[-1]["lattice_a"] * 100
    if isinstance(extreme, float) and not math.isfinite(extreme):
        raise ValueError(
            f"{rows[-1]['material_id']}: lattice_a * 100 must remain finite; "
            "choose a different --limit or source"
        )
    rows[-1]["lattice_a"] = extreme
    rows.append(rows[-1].copy())
    return rows


def same_path(left: Path, right: Path) -> bool:
    """Recognize lexical aliases, symlinks (including parents), and hard links."""
    return left.resolve() == right.resolve() or (
        left.exists() and right.exists() and left.samefile(right)
    )


def validate_paths(source: Path, output: Path, clean_output: Path) -> None:
    """Validate both destinations before creating directories or writing either."""
    destinations = (("--output", output), ("--clean-output", clean_output))
    for flag, destination in destinations:
        if same_path(destination, source):
            raise ValueError(f"{flag} must not overwrite the source file: {source}")
    if same_path(output, clean_output):
        raise ValueError("--output and --clean-output must be different files")

    resolved_output, resolved_clean = output.resolve(), clean_output.resolve()
    if resolved_output in resolved_clean.parents or resolved_clean in resolved_output.parents:
        raise ValueError("--output and --clean-output cannot be parent/child paths")

    for flag, destination in destinations:
        if destination.suffix.lower() != ".json":
            raise ValueError(f"{flag} must have a .json extension: {destination}")
        resolved = destination.resolve()
        if resolved.exists() and not resolved.is_file():
            raise ValueError(f"{flag} must name a JSON file, not a directory or device: {destination}")
        for parent in resolved.parents:
            if parent.exists() and not parent.is_dir():
                raise ValueError(f"{flag} parent must be a directory: {parent}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="JSON object mapping IDs to structures")
    parser.add_argument(
        "--output", type=Path, default=Path("data/demo/structures_with_issues.json"),
        help="issues JSON destination (default: %(default)s)",
    )
    parser.add_argument(
        "--clean-output", type=Path, default=Path("data/demo/structures_flat.json"),
        help="clean JSON destination (default: %(default)s)",
    )
    parser.add_argument(
        "--limit", type=positive_int, default=20,
        help="maximum number of source structures (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    try:
        validate_paths(args.source, args.output, args.clean_output)
        data = json.loads(args.source.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict) or not data:
            raise ValueError("source must be a nonempty JSON object mapping IDs to structures")
        clean_rows = [flatten(key, value) for key, value in islice(data.items(), args.limit)]
        rows = introduce_issues(clean_rows)

        # Serialize both datasets before writing so validation cannot leave half a demo.
        clean_json = json.dumps(clean_rows, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        issues_json = json.dumps(rows, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        for destination in (args.clean_output, args.output):
            destination.parent.mkdir(parents=True, exist_ok=True)
        args.clean_output.write_text(clean_json, encoding="utf-8")
        args.output.write_text(issues_json, encoding="utf-8")
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print(f"Wrote {len(clean_rows)} clean rows to {args.clean_output}")
    print(f"Wrote {len(rows)} rows (including one appended duplicate) to {args.output}")


if __name__ == "__main__":
    main()
