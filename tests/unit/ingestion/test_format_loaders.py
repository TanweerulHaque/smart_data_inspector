"""Format parsers are independently callable, not only through CLI integration."""

from decimal import Decimal

import pytest

from smart_data_inspector.ingestion.csv.loader import load_csv
from smart_data_inspector.ingestion.json.loader import load_json
from smart_data_inspector.loaders import load_dataset
from smart_data_inspector.models import InspectionError


def test_csv_parser_preserves_raw_quoted_values_and_header(tmp_path, rows):
    path = tmp_path / "input.csv"
    path.write_text('id,label\n001,"a,b"\n002,\n', encoding="utf-8")
    frame = load_csv(path)
    assert list(frame.columns) == ["id", "label"]
    assert rows(frame) == [["001", "a,b"], ["002", ""]]


def test_json_parser_unions_keys_and_retains_null_and_native_types(tmp_path, rows):
    path = tmp_path / "input.json"
    path.write_text('[{"a":1.25,"b":true},{"c":"hello","a":null}]')
    frame = load_json(path)
    assert list(frame.columns) == ["a", "b", "c"]
    assert rows(frame) == [[Decimal("1.25"), True, None], [None, None, "hello"]]


@pytest.mark.parametrize("text", ['[{"x":"\\ud800"}]', '[{"\\ud800":1}]'])
def test_lone_surrogate_json_lines_escapes_are_rejected_as_unsupported_unicode(tmp_path, text):
    path = tmp_path / "invalid.jsonl"
    path.write_text(text[1:-1])
    with pytest.raises(InspectionError, match="Unicode scalar"):
        load_dataset(path)
