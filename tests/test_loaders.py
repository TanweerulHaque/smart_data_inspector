"""Input validation and lossless loading, without third-party test dependencies."""

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from smart_data_inspector.loaders import InspectionError, load_dataset


class LoadDatasetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_csv_bom_case_insensitive_suffix_and_quoted_records(self):
        path = self.write(
            "measurements.CsV",
            '\ufeffid,description,flag\n001,"café, sample",TRUE\n\n'
            '1,"two\nlines",false\n,,\n',
        )
        dataset = load_dataset(path)
        self.assertEqual(dataset.source, path)
        self.assertEqual(dataset.format, "CSV")
        self.assertEqual(dataset.columns, ["id", "description", "flag"])
        self.assertEqual(dataset.rows, [
            ["001", "café, sample", "TRUE"],
            ["1", "two\nlines", "false"],
            ["", "", ""],
        ])

    def test_csv_ignores_blank_physical_lines_before_the_header(self):
        dataset = load_dataset(self.write("leading-blanks.csv", "\n\nid,label\n\n1,alpha\n\n"))
        self.assertEqual(dataset.columns, ["id", "label"])
        self.assertEqual(dataset.rows, [["1", "alpha"]])

    def test_json_bom_preserves_scalars_and_first_seen_union_order(self):
        dataset = load_dataset(self.write(
            "records.JsOn",
            '\ufeff[{"label":"001","count":1,"flag":true},'
            '{"fraction":1.25,"label":"café","flag":false},'
            '{"count":null}]',
        ))
        self.assertEqual(dataset.format, "JSON")
        self.assertEqual(dataset.columns, ["label", "count", "flag", "fraction"])
        self.assertEqual(dataset.rows, [
            ["001", 1, True, None],
            ["café", None, False, Decimal("1.25")],
            [None, None, None, None],
        ])
        self.assertIs(type(dataset.rows[0][1]), int)
        self.assertIs(type(dataset.rows[0][2]), bool)
        self.assertIs(type(dataset.rows[1][3]), Decimal)

    def test_all_null_rows_are_not_an_empty_dataset(self):
        dataset = load_dataset(self.write("nulls.json", '[{"value":null},{}]'))
        self.assertEqual(dataset.columns, ["value"])
        self.assertEqual(dataset.rows, [[None], [None]])

    def test_rejects_invalid_csv_without_silently_dropping_records(self):
        cases = {
            "empty": "",
            "header_only": "a,b\n\n",
            "empty_header": "a,\n1,2\n",
            "whitespace_header": "a,  \n1,2\n",
            "duplicate_header": "a,a\n1,2\n",
            "short_row": "a,b\n1,2\n3\n",
            "long_row": "a,b\n1,2,3\n",
            "unterminated_quote": 'a,b\n1,"unfinished\n',
        }
        for name, text in cases.items():
            with self.subTest(case=name), self.assertRaises(InspectionError):
                load_dataset(self.write(name + ".csv", text))

    def test_rejects_unsupported_or_malformed_json(self):
        cases = {
            "empty": "[]",
            "no_columns": "[{}]",
            "object_root": '{"a":1}',
            "scalar_root": "null",
            "primitive_row": '[{"a":1},2]',
            "array_row": "[[1]]",
            "nested_object": '[{"a":{"b":1}}]',
            "nested_array": '[{"a":[1]}]',
            "malformed": '[{"a":1}',
            "json_lines": '{"a":1}\n{"a":2}\n',
            "duplicate_keys": '[{"a":1,"a":2}]',
            "escaped_duplicate_keys": '[{"a":1,"\\u0061":2}]',
            "empty_key": '[{"":1}]',
            "blank_key": '[{"  ":1}]',
            "nan": '[{"a":NaN}]',
            "infinity": '[{"a":Infinity}]',
            "negative_infinity": '[{"a":-Infinity}]',
        }
        for name, text in cases.items():
            with self.subTest(case=name), self.assertRaises(InspectionError):
                load_dataset(self.write(name + ".json", text))

    def test_rejects_missing_directory_unsupported_and_non_utf8_inputs(self):
        directory = self.root / "directory.csv"
        directory.mkdir()
        invalid_utf8 = self.root / "invalid.csv"
        invalid_utf8.write_bytes(b"name\n\xff\n")
        for path in (
            self.root / "absent.csv",
            directory,
            self.write("records.txt", "a\n1\n"),
            invalid_utf8,
        ):
            with self.subTest(path=path.name), self.assertRaises(InspectionError):
                load_dataset(path)


if __name__ == "__main__":
    unittest.main()
