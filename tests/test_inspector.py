"""Exact summaries and quality-rule behavior for the public inspection API."""

import json
import math
import tempfile
import unittest
from pathlib import Path

from smart_data_inspector.inspector import InspectionConfig, inspect_dataset
from smart_data_inspector.loaders import load_dataset
from smart_data_inspector.models import Dataset


class InspectionConfigTests(unittest.TestCase):
    def test_defaults_and_valid_boundaries(self):
        config = InspectionConfig()
        self.assertEqual(config.missing_threshold, 0.05)
        self.assertEqual(config.top_values, 5)
        self.assertEqual(config.iqr_multiplier, 1.5)
        self.assertEqual(set(config.missing_values), {"", "NA", "N/A", "n/a", "#N/A", "NULL", "null", "NaN", "nan"})
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
                         ["integer", "number", "boolean", "string", "string"])
        integer = columns["integer"]
        self.assertEqual(integer.type_counts, {"integer": 4})
        self.assertEqual(integer.distinct_count, 3)
        self.assertEqual(integer.top_values[0], ("1", 2))
        self.assertCountEqual(integer.top_values, [("1", 2), ("001", 1), ("01", 1)])
        assert integer.numeric is not None
        assert integer.numeric.mean is not None
        self.assertAlmostEqual(integer.numeric.mean, 1.0)
        number = columns["number"].numeric
        assert number is not None
        self.assertEqual(number.count, 4)
        self.assertEqual((number.minimum, number.maximum, number.mean),
                         (-0.5, 3.0, 1.5))
        self.assertEqual(columns["boolean"].type_counts, {"boolean": 4})
        self.assertIsNone(columns["boolean"].numeric)
        self.assertEqual(columns["label"].distinct_count, 3)
        self.assertEqual(columns["label"].top_values[0], ("red", 2))
        self.assertCountEqual(columns["label"].top_values, [("red", 2), ("blue", 1), ("green", 1)])
        self.assertIsNone(columns["label"].numeric)
        mixed = columns["mixed"]
        self.assertEqual(mixed.type_counts, {"integer": 1, "string": 1, "number": 1})
        self.assertEqual((mixed.missing_count, mixed.missing_fraction), (1, 0.25))
        self.assertIsNone(mixed.numeric)
        self.assertEqual(mixed.unexpected_values, [])
        self.assertIn(("High missingness", "mixed"), {(finding.check_name, finding.column) for finding in inspection.findings})

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
        self.assertNotIsInstance(column.top_values[0][0], (str, bool))
        assert column.numeric is not None
        self.assertEqual(column.numeric.count, 3)
        self.assertEqual((column.numeric.minimum, column.numeric.maximum), (0.0, 1.0))

    def test_json_strings_are_not_inferred_as_numbers_or_booleans(self):
        inspection = inspect_dataset(self.load('[{"v":"1"},{"v":"1.5"},{"v":"true"}]'))
        column = inspection.columns[0]
        self.assertEqual(column.inferred_type, "string")
        self.assertEqual(column.type_counts, {"string": 3})
        self.assertIsNone(column.numeric)

    def test_numeric_mean_is_accurate_within_floating_point_tolerance(self):
        column = inspect_dataset(self.load('[{"v":0.1},{"v":0.2},{"v":0.3}]')).columns[0]
        self.assertEqual(column.inferred_type, "number")
        assert column.numeric is not None
        assert column.numeric.minimum is not None
        assert column.numeric.maximum is not None
        assert column.numeric.mean is not None
        self.assertAlmostEqual(column.numeric.minimum, 0.1)
        self.assertAlmostEqual(column.numeric.maximum, 0.3)
        self.assertAlmostEqual(column.numeric.mean, 0.2)

    def test_large_finite_numbers_have_a_finite_mean_without_sum_overflow(self):
        for text, suffix in (
            ("v\n1e308\n1e308\n", "csv"),
            ('[{"v":1e308},{"v":1e308}]', "json"),
        ):
            with self.subTest(format=suffix):
                numeric = inspect_dataset(self.load(text, suffix)).columns[0].numeric
                assert numeric is not None
                assert numeric.mean is not None
                self.assertEqual(numeric.count, 2)
                self.assertEqual((numeric.minimum, numeric.maximum), (1e308, 1e308))
                self.assertTrue(math.isclose(numeric.mean, 1e308, rel_tol=1e-14))
                self.assertTrue(math.isfinite(numeric.mean))

    def test_numeric_mean_preserves_small_values_during_cancellation(self):
        for text, suffix in (
            ("v\n1e30\n1\n-1e30\n", "csv"),
            ('[{"v":1e30},{"v":1},{"v":-1e30}]', "json"),
        ):
            with self.subTest(format=suffix):
                numeric = inspect_dataset(self.load(text, suffix)).columns[0].numeric
                assert numeric is not None
                assert numeric.mean is not None
                self.assertEqual(numeric.count, 3)
                self.assertEqual((numeric.minimum, numeric.maximum), (-1e30, 1e30))
                self.assertAlmostEqual(numeric.mean, 1 / 3)
                self.assertTrue(math.isfinite(numeric.mean))

    def test_default_missing_markers_exclude_zero_and_false(self):
        values = [None, "", " \t", "NA", " n/a ", "NULL", " null ", "NaN", 0, False, "ok"]
        dataset = self.load(json.dumps([{"v":value} for value in values]))
        inspection = inspect_dataset(dataset)
        column = inspection.columns[0]
        self.assertEqual(column.missing_count, 8)
        self.assertAlmostEqual(column.missing_fraction, 8 / 11)
        self.assertEqual(column.distinct_count, 3)
        self.assertEqual(column.type_counts, {"integer": 1, "boolean": 1, "string": 1})
        self.assertEqual(dataset.frame["v"].iloc[8:].tolist(), [0, False, "ok"])
        self.assertEqual(inspection.config, InspectionConfig())

    def test_custom_missing_markers_replace_defaults_and_are_case_sensitive(self):
        values = [None, "", " \t", " MISSING ", "N/A", "NA", "null", "nan", "none", "Straße", "STRASSE"]
        dataset = self.load(json.dumps([{"v":value} for value in values]))
        column = inspect_dataset(dataset, InspectionConfig(
            missing_values=(" MISSING ", "Straße"), top_values=10,
        )).columns[0]
        self.assertEqual(column.missing_count, 5)
        self.assertEqual(column.type_counts, {"string": 6})
        self.assertEqual(column.distinct_count, 6)
        self.assertEqual({value for value, _ in column.top_values}, {"N/A", "NA", "null", "nan", "none", "STRASSE"})
        self.assertEqual(column.marker_conversions, {"": 2, "MISSING": 1, "Straße": 1})

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
        duplicate_findings = [finding for finding in inspection.findings if finding.check_name == "Duplicate rows"]
        self.assertEqual(len(duplicate_findings), 1)
        self.assertIsNone(duplicate_findings[0].column)
        self.assertTrue(duplicate_findings[0].message)

    def test_missing_threshold_is_inclusive_and_configurable(self):
        dataset = self.load('[{"v":null},{"v":1},{"v":2},{"v":3},{"v":4}]')
        for threshold, expected_count in ((0.2, 1), (0.200001, 0), (1, 0)):
            with self.subTest(threshold=threshold):
                result = inspect_dataset(dataset, InspectionConfig(missing_threshold=threshold))
                self.assertEqual(sum(f.check_name == "High missingness" for f in result.findings), expected_count)
        all_null = inspect_dataset(self.load('[{"v":null},{}]'), InspectionConfig(missing_threshold=1))
        self.assertIn("High missingness", [finding.check_name for finding in all_null.findings])
        self.assertEqual(all_null.duplicate_rows, 1)

    def test_dominantly_numeric_csv_has_subset_until_threshold_is_raised(self):
        dataset = self.load("measurement\n1\n2\n3\n4\nbad\nNA\n", "csv")
        result = inspect_dataset(dataset)
        column = result.columns[0]
        self.assertEqual(column.inferred_type, "mixed")
        self.assertEqual(column.unexpected_values, ["bad"])
        assert column.numeric is not None
        assert column.numeric.mean is not None
        self.assertEqual(column.numeric.count, 4)
        self.assertAlmostEqual(column.numeric.mean, 2.5)
        self.assertIn("Mixed value types", [f.check_name for f in result.findings])
        categorical = inspect_dataset(dataset, InspectionConfig(mixed_numeric_threshold=0.81))
        self.assertEqual(categorical.columns[0].inferred_type, "string")
        self.assertIsNone(categorical.columns[0].numeric)
        self.assertNotIn("Mixed value types", [f.check_name for f in categorical.findings])

    def test_nonfinite_csv_values_are_excluded_and_have_an_explicit_finding(self):
        dataset = self.load("v\n1\n+inf\n-inf\n3\n", "csv")
        result = inspect_dataset(dataset)
        column = result.columns[0]
        self.assertEqual(column.missing_count, 0)
        assert column.numeric is not None
        assert column.numeric.mean is not None
        self.assertEqual((column.numeric.count, column.numeric.nonfinite_count), (2, 2))
        self.assertAlmostEqual(column.numeric.mean, 2.0)
        self.assertEqual([(f.check_name, f.column) for f in result.findings],
                         [("Non-finite numeric values", "v")])
        self.assertIn("2 numeric value(s)", result.findings[0].evidence)

    def test_findings_keep_check_identity_separate_from_rule_expression(self):
        inspection = inspect_dataset(self.load('[{"v":null},{"v":1}]'))
        finding = next(f for f in inspection.findings if f.check_name == "High missingness")
        self.assertEqual(finding.column, "v")
        self.assertEqual(finding.severity, "warning")
        self.assertIn(">= 5.0%", finding.rule)
        self.assertIn("1 missing of 2", finding.evidence)
        self.assertIn(finding.evidence, finding.message)
        self.assertIn(finding.explanation, finding.message)

    def test_source_file_is_never_modified_and_configurations_are_independent(self):
        text = 'v,label\n1, NA \n2,ok\n3,ok\n100, NA \n'
        dataset = self.load(text, 'csv')
        source_bytes = dataset.source.read_bytes()
        first = inspect_dataset(dataset)
        second = inspect_dataset(self.load(text, 'csv'), InspectionConfig(
            missing_values=("ok",), top_values=1, iqr_multiplier=3))
        self.assertEqual(dataset.source.read_bytes(), source_bytes)
        self.assertEqual(first.columns[1].top_values, [("ok", 2)])
        self.assertEqual(first.columns[1].marker_conversions, {"NA": 2})
        self.assertEqual(second.columns[1].top_values, [(" NA ", 2)])
        self.assertEqual(first.config, InspectionConfig())
        self.assertEqual(first.columns, inspect_dataset(self.load(text, 'csv')).columns)

    def test_zero_rows_are_safe_for_the_reusable_api(self):
        dataset = Dataset.from_rows(self.root / "not-on-disk.csv", "CSV", ["v", "label"], [])
        inspection = inspect_dataset(dataset)
        self.assertEqual(inspection.duplicate_rows, 0)
        self.assertEqual({finding.check_name for finding in inspection.findings}, {"All-null column", "Potential duplicate columns"})
        self.assertIsNone(inspection.file_size_bytes)
        self.assertGreaterEqual(inspection.memory_bytes, 0)
        self.assertEqual([column.name for column in inspection.columns], ["v", "label"])
        for column in inspection.columns:
            self.assertEqual(column.inferred_type, "empty")
            self.assertEqual((column.missing_count, column.non_null_count), (0, 0))
            self.assertEqual(column.missing_fraction, 0)
            self.assertEqual(column.top_values, [])
            self.assertIsNone(column.numeric)

    def test_numeric_identifier_skips_outliers_but_measurement_does_not(self):
        values = [1, 2, 3, 4, 100]
        dataset = self.load(json.dumps([{"sample_id":v, "measurement":v} for v in values]))
        inspection = inspect_dataset(dataset)
        identifier, measurement = inspection.columns
        self.assertTrue(identifier.likely_identifier)
        self.assertFalse(measurement.likely_identifier)
        self.assertIsNotNone(identifier.numeric)
        self.assertIn(("Potential numerical outliers", "measurement"), [(f.check_name, f.column) for f in inspection.findings])
        self.assertIn(("Potential duplicate columns", "measurement"), [(f.check_name, f.column) for f in inspection.findings])

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
