"""Nested JSON is rejected by default and flattened only on request."""

from decimal import Decimal

import pytest

from smart_data_inspector.loaders import load_dataset
from smart_data_inspector.models import InspectionError


def write(tmp_path, text):
    path = tmp_path / "input.json"
    path.write_text(text, encoding="utf-8")
    return path


def test_array_with_nested_objects_becomes_dotted_columns(tmp_path, rows):
    path = write(tmp_path, '[{"id":1,"lattice":{"a":1.5,"angles":{"alpha":90}}},{"id":2,"extra":true}]')
    dataset = load_dataset(path, flatten_json=True)
    assert dataset.format == "JSON"
    assert dataset.columns == ["id", "lattice.a", "lattice.angles.alpha", "extra"]
    assert rows(dataset.frame) == [[1, Decimal("1.5"), 90, None], [2, None, None, True]]


def test_mapping_of_records_gets_key_column_first(tmp_path, rows):
    path = write(tmp_path, '{"mp-1":{"charge":0.0,"lattice":{"a":2}},"mp-2":{"charge":1.0}}')
    dataset = load_dataset(path, flatten_json=True)
    assert dataset.columns == ["_key", "charge", "lattice.a"]
    assert rows(dataset.frame) == [["mp-1", Decimal("0.0"), 2], ["mp-2", Decimal("1.0"), None]]


def test_lists_and_empty_objects_become_compact_json_text(tmp_path, rows):
    path = write(tmp_path, '[{"xyz":[1.25,2,{"el":"C"}],"pbc":[true,null],"props":{}}]')
    dataset = load_dataset(path, flatten_json=True)
    assert rows(dataset.frame) == [['[1.25,2,{"el":"C"}]', "[true,null]", "{}"]]


def test_key_column_name_collision_is_explained(tmp_path):
    with pytest.raises(InspectionError, match="already has a '_key' field"):
        load_dataset(write(tmp_path, '{"r1":{"_key":"x"}}'), flatten_json=True)


@pytest.mark.parametrize("text, message", [
    ('{"r1":{"a":1},"r2":5}', "not an object"),
    ("42", "top-level array"),
    ('[{"a":1},[2]]', "is not an object"),
    ('[{"a.b":1,"a":{"b":2}}]', "ambiguous"),
    ('[{"a":{"a":1,"a":2}}]', "Duplicate JSON key"),
    ('[{"a":{"b":NaN}}]', "Invalid JSON"),
    ('[{"a":{"":1}}]', "empty column name"),
])
def test_flatten_rejections(tmp_path, text, message):
    with pytest.raises(InspectionError, match=message):
        load_dataset(write(tmp_path, text), flatten_json=True)


def test_empty_mapping_is_an_empty_dataset(tmp_path):
    with pytest.raises(InspectionError, match="Dataset is empty"):
        load_dataset(write(tmp_path, "{}"), flatten_json=True)


@pytest.mark.parametrize("text", ['[{"a":{"b":1}}]', '[{"a":[1]}]', '{"r1":{"a":1}}'])
def test_nested_json_without_flag_suggests_flatten_option(tmp_path, text):
    with pytest.raises(InspectionError, match="Re-run with --flatten-json"):
        load_dataset(write(tmp_path, text))


def test_flat_json_is_unchanged_by_the_flag(tmp_path, rows):
    path = write(tmp_path, '[{"a":1,"b":"x"},{"b":null}]')
    assert rows(load_dataset(path, flatten_json=True).frame) == rows(load_dataset(path).frame)


def test_json_lines_load_and_flatten(tmp_path, rows):
    path = tmp_path / "input.jsonl"
    path.write_text('{"a":1,"b":{"c":2}}\n\n{"a":2.5}\n', encoding="utf-8")
    dataset = load_dataset(path, flatten_json=True)
    assert dataset.format == "JSONL"
    assert dataset.columns == ["a", "b.c"]
    assert rows(dataset.frame) == [[1, 2], [Decimal("2.5"), None]]
    with pytest.raises(InspectionError, match="line 2"):
        path.write_text('{"a":1}\n{"a":\n', encoding="utf-8")
        load_dataset(path)


def test_large_json_arrays_are_refused_with_a_conversion_hint(tmp_path, monkeypatch):
    from smart_data_inspector.ingestion.json import loader
    monkeypatch.setattr(loader, "MAX_JSON_BYTES", 10)
    with pytest.raises(InspectionError, match="JSON Lines"):
        load_dataset(write(tmp_path, '[{"a":1},{"a":2}]'))
