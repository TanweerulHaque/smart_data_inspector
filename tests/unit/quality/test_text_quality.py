from smart_data_inspector.config import InspectionConfig
from smart_data_inspector.inspector import inspect_dataset
from smart_data_inspector.models import Dataset


def test_rare_categories_are_found_even_when_not_in_truncated_top_values(tmp_path):
    rows = [["common"] for _ in range(98)] + [["rare_one"], ["rare_two"]]
    dataset = Dataset.from_rows(tmp_path / "labels.csv", "CSV", ["label"], rows)
    result = inspect_dataset(dataset, InspectionConfig(top_values=1, rare_category_threshold=0.02))
    finding = next(item for item in result.findings if item.check_name == "Rare categories")
    assert "2 category value(s)" in finding.evidence
