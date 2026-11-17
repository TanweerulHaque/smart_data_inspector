"""Demo preparation tests, deliberately independent of the inspection engine."""

import copy
import importlib.util
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "scripts" / "prepare_demo_data.py"
WRAPPER = PROJECT_ROOT / "examples" / "prepare_demo.py"
SPEC = importlib.util.spec_from_file_location("prepare_demo_data", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
DEMO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DEMO)
COLUMNS = [
    "material_id", "lattice_a", "lattice_b", "lattice_c", "lattice_alpha",
    "lattice_beta", "lattice_gamma", "lattice_volume", "num_sites",
    "num_distinct_elements", "elements",
]
LATTICE_FIELDS = ("a", "b", "c", "alpha", "beta", "gamma", "volume")


@pytest.fixture
def structure():
    return {
        "lattice": {
            "a": 2.0, "b": 3, "c": 4.5, "alpha": 90.0, "beta": 91,
            "gamma": 120.0, "volume": 24.0, "matrix": [[1, 0, 0]],
        },
        "sites": [
            {"species": [{"element": "O"}, {"element": "Ti"}], "abc": [0, 0, 0]},
            {"species": [{"element": "Ba"}, {"element": "O"}]},
        ],
        "properties": {"ignored": ["nested"]},
    }


def source_records(structure, count=20):
    records = {}
    for index in range(count):
        record = copy.deepcopy(structure)
        record["lattice"]["a"] += index / 10
        records[f"mp-{index:03d}"] = record
    return records


@pytest.fixture
def source(tmp_path, structure):
    path = tmp_path / "source.json"
    path.write_text(json.dumps(source_records(structure, 25)), encoding="utf-8")
    return path


def run_cli(tmp_path, *arguments, script=SCRIPT):
    return subprocess.run(
        [sys.executable, "-B", str(script), *map(str, arguments)],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8",
        check=False, timeout=15,
    )


def assert_error(result, text):
    assert result.returncode == 2, result.stdout + result.stderr
    assert text in result.stderr
    assert "Traceback" not in result.stderr
    assert result.stdout == ""


def read_outputs(tmp_path):
    clean = tmp_path / "data/demo/structures_flat.json"
    issues = tmp_path / "data/demo/structures_with_issues.json"
    return json.loads(clean.read_text()), json.loads(issues.read_text())


def test_flatten_exact_features_without_mutating_structure(structure):
    original = copy.deepcopy(structure)
    row = DEMO.flatten("mp-café", structure)
    assert list(row) == COLUMNS
    assert row == {
        "material_id": "mp-café", "lattice_a": 2.0, "lattice_b": 3,
        "lattice_c": 4.5, "lattice_alpha": 90.0, "lattice_beta": 91,
        "lattice_gamma": 120.0, "lattice_volume": 24.0, "num_sites": 2,
        "num_distinct_elements": 3, "elements": "Ba, O, Ti",
    }
    assert structure == original
    assert all(isinstance(value, (str, int, float)) for value in row.values())
    structure["charge"] = "ignored: not one of the eleven features"
    assert DEMO.flatten("mp-café", structure) == row


def test_flatten_normalizes_elements_and_counts_empty_sites(structure):
    structure["sites"] = [{"species": [{"element": " Ti "}, {"element": "Ti"}]}]
    row = DEMO.flatten("mp-test", structure)
    assert (row["num_sites"], row["num_distinct_elements"], row["elements"]) == (1, 1, "Ti")
    structure["sites"] = []
    row = DEMO.flatten("mp-test", structure)
    assert (row["num_sites"], row["num_distinct_elements"], row["elements"]) == (0, 0, "")


@pytest.mark.parametrize("field", LATTICE_FIELDS)
@pytest.mark.parametrize("bad", [None, True, False, "2", [], {}, math.nan, math.inf, -math.inf])
def test_flatten_rejects_invalid_numeric_features(structure, field, bad):
    structure["lattice"][field] = bad
    with pytest.raises(ValueError, match=f"mp-test: lattice_{field} must be a finite number"):
        DEMO.flatten("mp-test", structure)


@pytest.mark.parametrize("field", LATTICE_FIELDS)
def test_flatten_requires_every_lattice_feature(structure, field):
    del structure["lattice"][field]
    with pytest.raises(ValueError, match=f"lattice_{field}"):
        DEMO.flatten("mp-test", structure)


@pytest.mark.parametrize("material_id", ["", "  ", None, 1])
def test_flatten_rejects_invalid_material_id(structure, material_id):
    with pytest.raises(ValueError, match="material_id"):
        DEMO.flatten(material_id, structure)


@pytest.mark.parametrize("record", [None, [], 1, {}, {"lattice": [], "sites": []},
                                         {"lattice": {}, "sites": {}}])
def test_flatten_rejects_invalid_structure_shape(record):
    with pytest.raises(TypeError, match="mp-test"):
        DEMO.flatten("mp-test", record)


@pytest.mark.parametrize("site", [None, [], {}, {"species": []}, {"species": {}},
    {"species": [None]}, {"species": [{}]}, {"species": [{"element": None}]},
    {"species": [{"element": 1}]}, {"species": [{"element": "  "}]}])
def test_flatten_rejects_invalid_site_species(structure, site):
    structure["sites"] = [site]
    with pytest.raises(ValueError, match="mp-test: site 0"):
        DEMO.flatten("mp-test", structure)


@pytest.mark.parametrize("count", [1, 2, 3, 4, 5, 7, 20, 21])
def test_issue_injection_is_exact_and_preserves_clean_rows(structure, count):
    clean = [DEMO.flatten(key, value) for key, value in source_records(structure, count).items()]
    original = copy.deepcopy(clean)
    issues = DEMO.introduce_issues(clean)
    expected = copy.deepcopy(clean)
    missing_count = math.ceil(count / 4)
    for index in range(missing_count):
        if index % 2:
            expected[index]["lattice_volume"] = None
        else:
            del expected[index]["lattice_volume"]
    if missing_count < count:
        expected[missing_count]["lattice_volume"] = "not measured"
    expected[-1]["lattice_a"] *= 100
    expected.append(expected[-1].copy())
    assert clean == original
    assert issues == expected
    assert issues[-1] == issues[-2]
    assert issues[-1] is not issues[-2]
    assert all(row is not clean[index] for index, row in enumerate(issues[:-1]))
    assert issues == DEMO.introduce_issues(clean)


def test_introduced_extreme_exceeds_iqr_upper_fence(structure):
    clean = [DEMO.flatten(key, value) for key, value in source_records(structure).items()]
    issues = DEMO.introduce_issues(clean)
    values = [row["lattice_a"] for row in issues]
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    assert values[-1] > q3 + 1.5 * (q3 - q1)
    assert values[-2] == values[-1] == clean[-1]["lattice_a"] * 100


def test_issue_injection_rejects_empty_input_and_overflow(structure):
    with pytest.raises(ValueError, match="at least one clean row"):
        DEMO.introduce_issues([])
    structure["lattice"]["a"] = 1e308
    clean = [DEMO.flatten("mp-test", structure)]
    with pytest.raises(ValueError, match=r"lattice_a \* 100 must remain finite"):
        DEMO.introduce_issues(clean)
    assert clean[0]["lattice_a"] == 1e308
    assert clean[0]["lattice_volume"] == 24.0


def test_cli_defaults_determinism_and_compatibility_wrapper(tmp_path, source):
    before = source.read_bytes()
    result = run_cli(tmp_path, source)
    assert result.returncode == 0, result.stderr
    assert "20 clean rows" in result.stdout
    assert "21 rows (including one appended duplicate)" in result.stdout
    clean, issues = read_outputs(tmp_path)
    assert len(clean) == 20 and len(issues) == 21
    assert [row["material_id"] for row in clean] == list(json.loads(before))[:20]
    assert all(list(row) == COLUMNS for row in clean)
    assert issues == DEMO.introduce_issues(clean)
    paths = [tmp_path / "data/demo" / name for name in
             ("structures_flat.json", "structures_with_issues.json")]
    original_bytes = [path.read_bytes() for path in paths]
    for script in (SCRIPT, WRAPPER):
        result = run_cli(tmp_path, source, script=script)
        assert result.returncode == 0, result.stderr
        assert [path.read_bytes() for path in paths] == original_bytes
    assert source.read_bytes() == before
    assert all(content.endswith(b"\n") for content in original_bytes)


@pytest.mark.parametrize("script", [SCRIPT, WRAPPER])
@pytest.mark.parametrize("limit", [1, 2, 5, 30])
def test_cli_limit_and_nested_explicit_destinations(tmp_path, source, limit, script):
    clean = tmp_path / "new/clean/flat.json"
    issues = tmp_path / "other/issues/flawed.JSON"
    result = run_cli(tmp_path, source, "--limit", limit, "--output", issues,
                     "--clean-output", clean, script=script)
    assert result.returncode == 0, result.stderr
    assert len(json.loads(clean.read_text())) == min(limit, 25)
    assert len(json.loads(issues.read_text())) == min(limit, 25) + 1
    assert not (tmp_path / "data").exists()


def test_cli_utf8_bom_and_non_ascii_values(tmp_path, structure):
    structure["sites"][0]["species"][0]["element"] = "café"
    source = tmp_path / "source.json"
    source.write_text(json.dumps({"mp-café": structure}, ensure_ascii=False), encoding="utf-8-sig")
    result = run_cli(tmp_path, source)
    assert result.returncode == 0, result.stderr
    clean, _ = read_outputs(tmp_path)
    assert clean[0]["material_id"] == "mp-café"
    assert "café" in clean[0]["elements"]
    assert b"caf\xc3\xa9" in (tmp_path / "data/demo/structures_flat.json").read_bytes()


@pytest.mark.parametrize("limit", ["0", "-1", "1.5", "nope"])
def test_cli_rejects_invalid_limits_without_writing(tmp_path, source, limit):
    result = run_cli(tmp_path, source, "--limit", limit)
    assert_error(result, "limit must be a positive integer")
    assert not (tmp_path / "data").exists()


@pytest.mark.parametrize("arguments, message", [
    ([], "source"), (["--unknown"], "unrecognized arguments"),
    (["--limit"], "expected one argument"), (["--output"], "expected one argument"),
    (["--clean-output"], "expected one argument"),
])
def test_cli_argument_errors(tmp_path, source, arguments, message):
    actual = arguments if not arguments else [source, *arguments]
    assert_error(run_cli(tmp_path, *actual), message)
    assert not (tmp_path / "data").exists()


@pytest.mark.parametrize("flag", ["--output", "--clean-output"])
@pytest.mark.parametrize("alias", ["direct", "relative", "symlink", "hardlink", "symlink-parent"])
def test_cli_protects_source_including_links(tmp_path, source, flag, alias):
    original = source.read_bytes()
    if alias == "direct":
        destination = source
    elif alias == "relative":
        destination = Path("data/../source.json")
        (tmp_path / "data").mkdir()
    elif alias == "symlink":
        destination = tmp_path / "source-alias.json"
        destination.symlink_to(source)
    elif alias == "hardlink":
        destination = tmp_path / "source-alias.json"
        destination.hardlink_to(source)
    else:
        parent = tmp_path / "linked-parent"
        parent.symlink_to(tmp_path, target_is_directory=True)
        destination = parent / source.name
    assert_error(run_cli(tmp_path, source, flag, destination), "must not overwrite the source")
    assert source.read_bytes() == original
    assert not (tmp_path / "data/demo").exists()


@pytest.mark.parametrize("flag", ["--output", "--clean-output"])
def test_cli_protects_symlink_source_target(tmp_path, source, flag):
    alias = tmp_path / "source-link.json"
    alias.symlink_to(source)
    original = source.read_bytes()
    assert_error(run_cli(tmp_path, alias, flag, source), "must not overwrite the source")
    assert source.read_bytes() == original


@pytest.mark.parametrize("alias", ["direct", "relative", "symlink", "hardlink", "dangling-symlink"])
def test_cli_outputs_must_be_distinct_including_links(tmp_path, source, alias):
    clean = tmp_path / "clean.json"
    if alias == "dangling-symlink":
        issues = tmp_path / "issues.json"
        issues.symlink_to(clean)
    else:
        clean.write_text("keep clean", encoding="utf-8")
        if alias == "direct":
            issues = clean
        elif alias == "relative":
            (tmp_path / "sub").mkdir()
            issues = tmp_path / "sub/../clean.json"
        else:
            issues = tmp_path / "issues.json"
            if alias == "symlink":
                issues.symlink_to(clean)
            else:
                issues.hardlink_to(clean)
    result = run_cli(tmp_path, source, "--output", issues, "--clean-output", clean)
    assert_error(result, "must be different files")
    if alias == "dangling-symlink":
        assert not clean.exists()
    else:
        assert clean.read_text() == "keep clean"


@pytest.mark.parametrize("reverse", [False, True])
def test_cli_outputs_cannot_be_parent_and_child(tmp_path, source, reverse):
    paths = [tmp_path / "parent.json", tmp_path / "parent.json/child.json"]
    if reverse:
        paths.reverse()
    assert_error(run_cli(tmp_path, source, "--output", paths[0], "--clean-output", paths[1]),
                 "cannot be parent/child paths")
    assert not (tmp_path / "parent.json").exists()


@pytest.mark.parametrize("flag", ["--output", "--clean-output"])
@pytest.mark.parametrize("kind", ["directory", "parent-file", "wrong-extension", "symlink-loop"])
def test_cli_rejects_invalid_destinations_before_writing(tmp_path, source, flag, kind):
    protected = tmp_path / "protected.json"
    protected.write_text("keep existing output", encoding="utf-8")
    destination = tmp_path / "invalid.json"
    if kind == "directory":
        destination.mkdir()
        message = "must name a JSON file"
    elif kind == "parent-file":
        parent = tmp_path / "parent"
        parent.write_text("keep parent", encoding="utf-8")
        destination = parent / "child.json"
        message = "parent must be a directory"
    elif kind == "wrong-extension":
        destination = tmp_path / "invalid.txt"
        message = ".json extension"
    else:
        destination.symlink_to(destination)
        message = "error:"
    other = "--clean-output" if flag == "--output" else "--output"
    result = run_cli(tmp_path, source, flag, destination, other, protected)
    assert_error(result, message)
    assert protected.read_text() == "keep existing output"


@pytest.mark.parametrize("payload, message", [
    ("{", "Expecting"), ("{}", "nonempty JSON object"), ("[]", "nonempty JSON object"),
    ("null", "nonempty JSON object"), ('{"mp-test":null}', "structure must be an object"),
    ('{"mp-test":{"lattice":{},"sites":[]}}', "lattice_a must be a finite number"),
])
def test_cli_bad_source_preserves_both_outputs(tmp_path, payload, message):
    source = tmp_path / "bad.json"
    source.write_text(payload, encoding="utf-8")
    clean, issues = tmp_path / "clean.json", tmp_path / "issues.json"
    for path in (clean, issues):
        path.write_text("keep existing output", encoding="utf-8")
    result = run_cli(tmp_path, source, "--output", issues, "--clean-output", clean)
    assert_error(result, message)
    assert all(path.read_text() == "keep existing output" for path in (clean, issues))
    assert source.read_text() == payload


@pytest.mark.parametrize("kind", ["absent", "directory", "invalid-utf8"])
def test_cli_source_file_errors_are_actionable(tmp_path, kind):
    source = tmp_path / "bad.json"
    if kind == "directory":
        source.mkdir()
    elif kind == "invalid-utf8":
        source.write_bytes(b"\xff")
    result = run_cli(tmp_path, source)
    assert_error(result, "error:")
    assert not (tmp_path / "data").exists()


def test_cli_validates_all_selected_records_before_writing(tmp_path, structure):
    records = source_records(structure, 2)
    records["mp-001"]["sites"] = [{}]
    source = tmp_path / "source.json"
    source.write_text(json.dumps(records), encoding="utf-8")
    result = run_cli(tmp_path, source)
    assert_error(result, "mp-001: site 0 needs a nonempty species array")
    assert not (tmp_path / "data").exists()
    result = run_cli(tmp_path, source, "--limit", 1)
    assert result.returncode == 0, result.stderr


def test_cli_overflow_does_not_create_outputs(tmp_path, structure):
    structure["lattice"]["a"] = 1e308
    source = tmp_path / "source.json"
    source.write_text(json.dumps({"mp-test": structure}), encoding="utf-8")
    assert_error(run_cli(tmp_path, source), "lattice_a * 100 must remain finite")
    assert not (tmp_path / "data").exists()
