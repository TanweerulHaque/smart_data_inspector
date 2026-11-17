"""Exact summaries and quality-rule behavior for the public inspection API."""

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from smart_data_inspector.inspector import InspectionConfig, inspect_dataset
from smart_data_inspector.loaders import load_dataset


class InspectionConfigTests(unittest.TestCase):
    def test_defaults_and_valid_boundaries(self):
        config = InspectionConfig()
        self.assertEqual(config.missing_threshold, 0.2)
        self.assertEqual(config.top_values, 3)
        self.assertEqual(set(config.missing_values), {"", "na", "n/a", "null", "none", "nan"})
        self.assertEqual(InspectionConfig(missing_threshold=1, top_values=1).top_values, 1)

    def test_rejects_out_of_range_and_nonfinite_thresholds(self):
        for threshold in (0, -0.1, 1.01, float("nan"), float("inf"), -float("inf")):
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                InspectionConfig(missing_threshold=threshold)

    def test_rejects_nonpositive_top_values(self):
        for top_values in (0, -1):
            with self.subTest(top_values=top_values), self.assertRaises(ValueError):
                InspectionConfig(top_values=top_values)


class InspectDatasetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def load(self, text, suffix="json"):
        path = self.root / ("input." + suffix)
        path.write_text(text, encoding="utf-8")
        return load_dataset(path)

    def test_csv_inference_counts_and_numeric_summaries(self):
        inspection = inspect_dataset(self.load(
            "integer,number,boolean,label,mixed\n"
            "001,+1,true,red,1\n"
            "1,2.5,FALSE,blue,text\n"
            "01,3e0, True ,red,2.0\n"
            "1,-.5,false,green,\n",
            "csv",
        ))
        columns = {column.name: column for column in inspection.columns}
        self.assertEqual([column.inferred_type for column in inspection.columns],
                         ["integer", "number", "boolean", "string", "mixed"])
        integer = columns["integer"]
        self.assertEqual(integer.type_counts, {"integer": 4})
        self.assertEqual(integer.distinct_count, 3)
        self.assertEqual(integer.top_values[0], ("1", 2))
        self.assertCountEqual(integer.top_values, [("1", 2), ("001", 1), ("01", 1)])
        assert integer.numeric is not None
        self.assertEqual(integer.numeric.mean, Decimal(1))
        number = columns["number"].numeric
        assert number is not None
        self.assertEqual(number.count, 4)
        self.assertEqual((number.minimum, number.maximum, number.mean),
                         (Decimal("-.5"), Decimal(3), Decimal("1.5")))
        self.assertEqual(columns["boolean"].type_counts, {"boolean": 4})
        self.assertIsNone(columns["boolean"].numeric)
        self.assertEqual(columns["label"].distinct_count, 3)
        self.assertEqual(columns["label"].top_values[0], ("red", 2))
        self.assertCountEqual(columns["label"].top_values, [("red", 2), ("blue", 1), ("green", 1)])
        self.assertIsNone(columns["label"].numeric)
        mixed = columns["mixed"]
        self.assertEqual(mixed.type_counts, {"integer": 1, "string": 1, "number": 1})
        self.assertEqual((mixed.missing_count, mixed.missing_fraction), (1, 0.25))
        assert mixed.numeric is not None
        self.assertEqual((mixed.numeric.count, mixed.numeric.mean), (2, Decimal("1.5")))
        self.assertEqual({(finding.rule, finding.column) for finding in inspection.findings},
                         {("High missingness", "mixed"), ("Mixed value types", "mixed")})

    def test_csv_counts_and_duplicates_keep_original_strings(self):
        inspection = inspect_dataset(self.load("value\n001\n1\n1.0\n1\n TRUE \ntrue\n", "csv"))
        column = inspection.columns[0]
        self.assertEqual(inspection.duplicate_rows, 1)
        self.assertEqual(column.distinct_count, 5)
        self.assertEqual(column.top_values[0], ("1", 2))
        self.assertEqual(column.inferred_type, "mixed")

    def test_json_native_types_numeric_equivalence_and_boolean_separation(self):
        inspection = inspect_dataset(self.load(
            '[{"v":"1"},{"v":1},{"v":1.0},{"v":true},{"v":false},{"v":0}]'
        ))
        column = inspection.columns[0]
        self.assertEqual(column.inferred_type, "mixed")
        self.assertEqual(column.type_counts, {"string": 1, "integer": 2, "number": 1, "boolean": 2})
        self.assertEqual(column.distinct_count, 5)
        self.assertEqual(inspection.duplicate_rows, 1)
        self.assertEqual(column.top_values[0], (1, 2))
        self.assertIs(type(column.top_values[0][0]), int)
        assert column.numeric is not None
        self.assertEqual(column.numeric.count, 3)
        self.assertEqual((column.numeric.minimum, column.numeric.maximum), (Decimal(0), Decimal(1)))

    def test_json_strings_are_not_inferred_as_numbers_or_booleans(self):
        inspection = inspect_dataset(self.load('[{"v":"1"},{"v":"1.5"},{"v":"true"}]'))
        column = inspection.columns[0]
        self.assertEqual(column.inferred_type, "string")
        self.assertEqual(column.type_counts, {"string": 3})
        self.assertIsNone(column.numeric)

    def test_numeric_mean_uses_decimal_not_binary_float(self):
        column = inspect_dataset(self.load('[{"v":0.1},{"v":0.2},{"v":0.3}]')).columns[0]
        self.assertEqual(column.inferred_type, "number")
        assert column.numeric is not None
        self.assertEqual((column.numeric.minimum, column.numeric.maximum, column.numeric.mean),
                         (Decimal("0.1"), Decimal("0.3"), Decimal("0.2")))
        self.assertIsInstance(column.numeric.mean, Decimal)

    def test_large_finite_numbers_have_a_finite_decimal_mean(self):
        for text, suffix in (
            ("v\n1e308\n1e308\n", "csv"),
            ('[{"v":1e308},{"v":1e308}]', "json"),
        ):
            with self.subTest(format=suffix):
                numeric = inspect_dataset(self.load(text, suffix)).columns[0].numeric
                assert numeric is not None
                self.assertEqual(numeric.count, 2)
                self.assertEqual((numeric.minimum, numeric.maximum, numeric.mean),
                                 (Decimal("1e308"), Decimal("1e308"), Decimal("1e308")))
                self.assertIsInstance(numeric.mean, Decimal)
                self.assertTrue(numeric.mean.is_finite())

    def test_numeric_mean_preserves_small_values_during_cancellation(self):
        for text, suffix in (
            ("v\n1e30\n1\n-1e30\n", "csv"),
            ('[{"v":1e30},{"v":1},{"v":-1e30}]', "json"),
        ):
            with self.subTest(format=suffix):
                numeric = inspect_dataset(self.load(text, suffix)).columns[0].numeric
                assert numeric is not None
                self.assertEqual(numeric.count, 3)
                self.assertEqual((numeric.minimum, numeric.maximum),
                                 (Decimal("-1e30"), Decimal("1e30")))
                self.assertEqual(numeric.mean, Decimal(1) / 3)
                self.assertIsInstance(numeric.mean, Decimal)
                self.assertTrue(numeric.mean.is_finite())

    def test_default_missing_markers_exclude_zero_and_false_without_mutating_input(self):
        values = [None, "", " \t", "NA", " n/A ", "NULL", " none ", "NaN", 0, False, "ok"]
        dataset = self.load(json.dumps([{"v":value} for value in values]))
        original_rows = [row[:] for row in dataset.rows]
        inspection = inspect_dataset(dataset)
        column = inspection.columns[0]
        self.assertEqual(column.missing_count, 8)
        self.assertAlmostEqual(column.missing_fraction, 8 / 11)
        self.assertEqual(column.distinct_count, 3)
        self.assertEqual(column.type_counts, {"integer": 1, "boolean": 1, "string": 1})
        self.assertEqual(dataset.rows, original_rows)
        self.assertEqual(inspection.config, InspectionConfig())

    def test_custom_missing_markers_replace_defaults_and_casefold_unicode(self):
        values = [None, "", " \t", " MISSING ", "N/A", "NA", "null", "nan", "none", "Straße", "STRASSE"]
        dataset = self.load(json.dumps([{"v":value} for value in values]))
        column = inspect_dataset(dataset, InspectionConfig(
            missing_values=(" missing ", "strasse"), top_values=10,
        )).columns[0]
        self.assertEqual(column.missing_count, 6)
        self.assertEqual(column.type_counts, {"string": 5})
        self.assertEqual(column.distinct_count, 5)
        self.assertEqual({value for value, _ in column.top_values}, {"N/A", "NA", "null", "nan", "none"})

    def test_duplicates_normalize_missing_cells_across_entire_rows(self):
        inspection = inspect_dataset(self.load(
            '[{"a":null,"b":"x"},{"b":"x"},{"a":"NA","b":"x"},'
            '{"a":"","b":"x"},{"a":null,"b":"y"}]'
        ))
        self.assertEqual(inspection.duplicate_rows, 3)
        a, b = inspection.columns
        self.assertEqual((a.inferred_type, a.missing_count, a.distinct_count), ("empty", 5, 0))
        self.assertEqual(a.type_counts, {})
        self.assertEqual(a.top_values, [])
        self.assertIsNone(a.numeric)
        self.assertEqual(b.top_values, [("x", 4), ("y", 1)])
        duplicate_findings = [finding for finding in inspection.findings if finding.rule == "Duplicate rows"]
        self.assertEqual(len(duplicate_findings), 1)
        self.assertIsNone(duplicate_findings[0].column)
        self.assertTrue(duplicate_findings[0].message)

    def test_missing_threshold_is_inclusive_and_configurable(self):
        dataset = self.load('[{"v":null},{"v":1},{"v":2},{"v":3},{"v":4}]')
        for threshold, expected_count in ((0.2, 1), (0.200001, 0), (1, 0)):
            with self.subTest(threshold=threshold):
                result = inspect_dataset(dataset, InspectionConfig(missing_threshold=threshold))
                self.assertEqual(sum(f.rule == "High missingness" for f in result.findings), expected_count)
        all_null = inspect_dataset(self.load('[{"v":null},{}]'), InspectionConfig(missing_threshold=1))
        self.assertIn("High missingness", [finding.rule for finding in all_null.findings])
        self.assertEqual(all_null.duplicate_rows, 1)

    def test_top_values_respects_limit_and_excludes_missing_values(self):
        dataset = self.load('[{"v":"a"},{"v":"b"},{"v":"a"},{"v":"b"},{"v":"a"},{"v":"c"},{"v":null}]')
        column = inspect_dataset(dataset, InspectionConfig(top_values=1)).columns[0]
        self.assertEqual(column.top_values, [("a", 3)])
        self.assertEqual(column.distinct_count, 3)
        self.assertEqual(column.missing_count, 1)

    def test_clean_data_has_no_findings(self):
        inspection = inspect_dataset(self.load('[{"v":1,"name":"a"},{"v":2,"name":"b"}]'))
        self.assertEqual(inspection.duplicate_rows, 0)
        self.assertEqual(inspection.findings, [])


if __name__ == "__main__":
    unittest.main()
