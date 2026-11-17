
from smart_data_inspector.config import InspectionConfig
from smart_data_inspector.inspector import inspect_dataset
from smart_data_inspector.models import Dataset


def test_schema_check_finds_all_null_and_matching_columns(tmp_path):
    dataset = Dataset.from_rows(tmp_path / "input.csv", "CSV", ["a", "copy", "empty"], [[1, 1, None], [2, 2, None]])
    findings = inspect_dataset(dataset, InspectionConfig()).findings
    assert {(finding.check_name, finding.column) for finding in findings} >= {
        ("All-null column", "empty"), ("Potential duplicate columns", "copy")
    }
