import pandas as pd

from smart_data_inspector.profiling.relationships import profile_relationships


def test_relationships_return_pearson_and_rank_correlation_without_scipy():
    profile = profile_relationships(pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, 4, 6, 8]}), ["x", "y"])
    assert len(profile.relationships) == 1
    pair = profile.relationships[0]
    assert (pair.left, pair.right, pair.pair_count) == ("x", "y", 4)
    assert pair.pearson == 1.0
    assert pair.spearman == 1.0


def test_relationships_skip_constant_or_insufficient_pairs():
    profile = profile_relationships(pd.DataFrame({"x": [1, 1, None], "y": [2, 3, 4]}), ["x", "y"])
    assert profile.relationships == []
