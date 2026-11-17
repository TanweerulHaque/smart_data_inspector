"""Every test runs in its own temporary working directory.

The CLI writes to the current directory by default; this keeps test runs from ever
creating reports or chart folders inside the repository.
"""

import pytest


@pytest.fixture(autouse=True)
def _isolated_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def rows():
    """Turn a loaded frame into plain Python rows, with every missing value as None."""
    return table_rows


def table_rows(frame):
    import pandas as pd
    return [[None if pd.isna(value) else value for value in row]
            for row in frame.astype(object).itertuples(index=False)]
