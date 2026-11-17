"""Run the actual module entry point from the application project root."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HEADINGS = [
    "# Data Inspection Report",
    "## Overview",
    "## Overall summary",
    "## Schema inventory",
    "## Missing values",
    "## Duplicate rows",
    "## Numeric summaries",
    "## Categorical summaries",
    "## Data quality findings",
    "## Rules and limitations",
]


class CliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, "-m", "smart_data_inspector", "inspect", *map(str, arguments)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            check=False,
            text=True,
            encoding="utf-8",
            timeout=15,
        )

    def assert_error(self, result):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertTrue(result.stderr.strip())
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def successful_report(self, result, output):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn("Smart Data Inspector", result.stdout)
        self.assertIn("Rows:", result.stdout)
        self.assertIn("Columns:", result.stdout)
        self.assertIn("Additional duplicate rows:", result.stdout)
        self.assertIn("Missing cells:", result.stdout)
        self.assertIn("Approximate DataFrame memory:", result.stdout)
        # Rich may wrap long paths; ignore layout without treating stdout as a path.
        self.assertIn("Report:" + "".join(str(output).split()), "".join(result.stdout.split()))
        self.assertTrue(output.is_file())
        return output.read_text(encoding="utf-8")

    @staticmethod
    def section(report, heading):
        return report.split(heading, 1)[1].split("\n## ", 1)[0]

    def test_csv_default_report_success_even_with_quality_findings(self):
        source = self.write(
            "measurements.CSV",
            "\ufeffscore,category,unstable\n7,alpha,1\n11,alpha,text\n"
            "18,beta,2\nNA,beta,3\n7,alpha,1\n",
        )
        original = source.read_bytes()
        result = self.run_cli(source)
        report = self.successful_report(result, source.with_suffix(".report.md"))
        self.assertIn("Rows: 5 | Columns: 3 | Additional duplicate rows: 1", result.stdout)
        self.assertIn("Missing cells: 1", result.stdout)
        for heading in ("Severity", "Check", "Column", "Evidence"):
            self.assertIn(heading, result.stdout)
        self.assertEqual([line for line in report.splitlines() if line.startswith(("# ", "## "))], HEADINGS)
        for text in ("score", "category", "unstable", "10.75", "alpha", "beta"):
            self.assertIn(text, report)
        for rule in ("Duplicate rows", "High missingness", "Mixed value types"):
            self.assertIn(rule, self.section(report, "## Data quality findings"))
        self.assertEqual(source.read_bytes(), original)

    def test_json_bom_and_explicit_output_create_parent_directories(self):
        source = self.write("records.JsOn", '\ufeff[{"name":"café","value":1},{"value":3}]')
        output = self.root / "new" / "nested" / "inspection.md"
        report = self.successful_report(self.run_cli(source, "-o", output), output)
        for heading in HEADINGS:
            self.assertIn(heading, report.splitlines())
        self.assertIn("café", report)
        self.assertIn("value", report)
        self.assertFalse(source.with_suffix(".report.md").exists())

    def test_threshold_and_repeated_missing_values_replace_defaults(self):
        source = self.write("markers.json", json.dumps([
            {"v":value} for value in ("NA", "MISSING", "UNKNOWN", "", "ok")
        ]))
        output = self.root / "markers.md"
        options = ("--missing-value", "MISSING", "--missing-value", "UNKNOWN")
        cases = (("0.5", (), False), ("0.5", options, True), ("0.7", options, False))
        for threshold, missing_options, has_finding in cases:
            with self.subTest(threshold=threshold, missing_options=missing_options):
                report = self.successful_report(self.run_cli(
                    source, "-o", output, "--missing-threshold", threshold, *missing_options,
                ), output)
                findings = self.section(report, "## Data quality findings")
                self.assertEqual("| High missingness |" in findings, has_finding)
                self.assertEqual("| Missing values |" in findings, not has_finding)

    def test_top_values_option_limits_categorical_entries(self):
        source = self.write("categories.json", json.dumps([
            {"label":value} for value in ("TOP_A", "TOP_A", "TOP_A", "SECOND_B", "SECOND_B", "LAST_C")
        ]))
        output = self.root / "categories.md"
        report = self.successful_report(self.run_cli(source, "-o", output, "--top-values", "1"), output)
        categories = self.section(report, "## Categorical summaries")
        self.assertIn("TOP_A", categories)
        self.assertNotIn("SECOND_B", categories)
        self.assertNotIn("LAST_C", categories)

    def test_report_escapes_untrusted_column_names_and_cell_values(self):
        values = ["left|right", "*unsafe*", "[click](https://example.invalid)",
                  "<script>alert(1)</script>", "line one\n# injected"]
        source = self.write("untrusted.json", json.dumps([{"name|field":value} for value in values]))
        output = self.root / "safe.md"
        report = self.successful_report(self.run_cli(source, "-o", output, "--top-values", "5"), output)
        for raw in ("name|field", "left|right", "*unsafe*", "[click](https://example.invalid)", "<script>", "\n# injected"):
            with self.subTest(raw=raw):
                self.assertNotIn(raw, report)
        for text in ("left", "right", "unsafe", "click", "alert", "line one", "injected"):
            self.assertIn(text, report)

    def test_invalid_inputs_neither_create_nor_overwrite_reports(self):
        sources = [
            self.write("bad.csv", "a,b\n1\n"),
            self.write("bad.json", '[{"a":1}'),
            self.write("unsupported.txt", "a\n1\n"),
            self.root / "absent.csv",
        ]
        for index, source in enumerate(sources):
            for exists in (False, True):
                with self.subTest(source=source.name, existing_report=exists):
                    output = self.root / f"invalid-{index}-{exists}.md"
                    if exists:
                        output.write_text("keep existing report", encoding="utf-8")
                    self.assert_error(self.run_cli(source, "-o", output))
                    if exists:
                        self.assertEqual(output.read_text(encoding="utf-8"), "keep existing report")
                    else:
                        self.assertFalse(output.exists())
            self.assert_error(self.run_cli(source))
            self.assertFalse(source.with_suffix(".report.md").exists())

    def test_invalid_configuration_preserves_existing_report(self):
        source = self.write("valid.csv", "v\n1\n")
        output = self.write("existing.md", "keep existing report")
        options = [
            ("--missing-threshold", value) for value in ("0", "-0.1", "1.1", "nan", "inf", "-inf", "nope")
        ] + [("--top-values", value) for value in ("0", "-1", "1.5", "nope")] + [
            ("--iqr-multiplier", value) for value in ("0", "-1", "nan", "inf", "-inf", "nope")
        ]
        for option, value in options:
            with self.subTest(option=option, value=value):
                self.assert_error(self.run_cli(source, "-o", output, option, value))
                self.assertEqual(output.read_text(encoding="utf-8"), "keep existing report")
        self.assertFalse(source.with_suffix(".report.md").exists())

    def test_invalid_configuration_does_not_create_a_report(self):
        source = self.write("valid.csv", "v\n1\n")
        output = self.root / "not-created.md"
        self.assert_error(self.run_cli(source, "-o", output, "--top-values", "0"))
        self.assertFalse(output.exists())

    def test_requires_exactly_one_input(self):
        source = self.write("valid.csv", "v\n1\n")
        for arguments in ((), (source, source)):
            with self.subTest(arguments=arguments):
                self.assert_error(self.run_cli(*arguments))
        self.assertFalse(source.with_suffix(".report.md").exists())

    def test_invalid_output_extension_directory_and_parent_file(self):
        source = self.write("valid.csv", "v\n1\n")
        wrong_extension = self.write("existing.txt", "keep existing output")
        directory = self.root / "directory.md"
        directory.mkdir()
        parent_file = self.write("not-a-directory", "keep parent file")
        for output in (wrong_extension, directory, parent_file / "report.md"):
            with self.subTest(output=output):
                self.assert_error(self.run_cli(source, "-o", output))
        self.assertEqual(wrong_extension.read_text(encoding="utf-8"), "keep existing output")
        self.assertTrue(directory.is_dir())
        self.assertEqual(list(directory.iterdir()), [])
        self.assertEqual(parent_file.read_text(encoding="utf-8"), "keep parent file")
        self.assertEqual(source.read_text(encoding="utf-8"), "v\n1\n")

    def test_input_overwrite_guard_covers_same_path_symlinks_and_hardlinks(self):
        source = self.write("valid.csv", "v\n1\n")
        original = source.read_bytes()
        symlink = self.root / "symlink.md"
        symlink.symlink_to(source)
        hardlink = self.root / "hardlink.md"
        hardlink.hardlink_to(source)
        for output in (source, symlink, hardlink):
            with self.subTest(output=output.name):
                self.assert_error(self.run_cli(source, "-o", output))
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
