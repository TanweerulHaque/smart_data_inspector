import pandas as pd

from smart_data_inspector.config import InspectionConfig
from smart_data_inspector.profiling.missingness_analysis import profile_missingness_patterns


def test_missingness_patterns_capture_rows_pairs_and_repeated_sets():
    frame = pd.DataFrame({"a": [None, None, 1], "b": [None, None, 2], "c": [3, None, 4]})
    profile = profile_missingness_patterns(frame, InspectionConfig(row_missing_threshold=0.5))
    assert profile.total_missing == 5
    assert profile.row_missing_counts == [2, 3, 0]
    assert profile.high_missing_rows == 2
    assert profile.cooccurrences[0] == ("a", "b", 2)
    assert profile.patterns[0].columns == ("a", "b")
