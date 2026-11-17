import pandas as pd

from smart_data_inspector.profiling.text import profile_text


def test_text_summary_reports_formatting_evidence_without_mutation():
    series = pd.Series([" Red", "RED", "red", None])
    summary = profile_text(series)
    assert summary is not None
    assert (summary.count, summary.whitespace_count, summary.casefold_collision_count) == (3, 1, 1)
    assert series.iloc[:3].tolist() == [" Red", "RED", "red"]
