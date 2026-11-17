from datetime import date, datetime, timezone

import pandas as pd

from smart_data_inspector.models import ColumnSummary
from smart_data_inspector.profiling.dates import profile_datetime
from smart_data_inspector.quality.dates import check_dates

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_range_future_invalid_and_formats():
    values = ["2024-01-05", "2024-01-06T10:00:00", "2031-05-01", "2024-02-30", "05/01/2024",
              "2024-03-01T10:00:00+08:00", None]
    summary = profile_datetime(pd.Series(values, dtype=object), NOW)
    assert (summary.count, summary.minimum, summary.maximum) == (4, "2024-01-05T00:00:00", "2031-05-01T00:00:00")
    assert (summary.future_count, summary.invalid_count, summary.non_iso_count) == (1, 1, 1)
    assert summary.formats == {"YYYY-MM-DD": 3, "YYYY-MM-DDTHH:MM:SS": 1, "YYYY-MM-DDTHH:MM:SS+TZ": 1,
                               "non-ISO date text": 1}
    assert (summary.timezone_aware_count, summary.naive_count) == (1, 3)


def test_native_dates_and_no_dates():
    summary = profile_datetime(pd.Series([date(2025, 12, 31), datetime(2026, 2, 1)], dtype=object), NOW)
    assert summary.future_count == 1 and summary.formats == {"native date": 1, "native datetime": 1}
    assert profile_datetime(pd.Series(["a", "b"], dtype=object), NOW) is None


def test_date_checks_explain_each_problem():
    summary = profile_datetime(pd.Series(["2024-01-05", "2031-05-01", "2024-13-01", "5/1/2024"], dtype=object), NOW)
    column = ColumnSummary("when", "mixed", 0, 0, 4, 4, {}, [], None, datetime=summary)
    assert {finding.check_name for finding in check_dates(column)} == {
        "Future dates", "Invalid calendar dates", "Mixed date formats"}
