"""Date/time summaries: range, future values, invalid calendar dates and format mix.

Inference stays conservative (only ISO-like text or native date/time values count as
dates), but other date-looking text in the same column is reported as a format problem.
Naive values are compared as UTC; aware values are converted to UTC.
"""

import re
from datetime import date, datetime, timezone

import numpy as np
import pandas as pd

from ..models import DatetimeSummary
from .schema.profiler import ISO_DATE

# Common non-ISO spellings; reported as format inconsistencies, never parsed (they are ambiguous).
NON_ISO_DATE = re.compile(
    r"(?:\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\d{4}/\d{1,2}/\d{1,2}|\d{8}"
    r"|\d{1,2}\s+[A-Za-z]{3,9}\.?\s+\d{4}|[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4})"
    r"(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?\Z"
)


def _iso_format(text: str) -> str:
    """Describe the ISO shape, e.g. 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS+TZ'."""
    if len(text) == 10:
        return "YYYY-MM-DD"
    time = text[11:]
    zone = ""
    if time.endswith("Z"):
        zone, time = "Z", time[:-1]
    elif "+" in time or "-" in time:
        zone, time = "+TZ", re.split(r"[+-]", time, maxsplit=1)[0]
    shape = "HH:MM" + (":SS" if time.count(":") >= 2 else "") + (".fff" if "." in time else "")
    return f"YYYY-MM-DD{text[10]}{shape}{zone}"


def _parse(value: object) -> tuple[datetime | None, str | None]:
    """Return (UTC-naive timestamp, format label); (None, label) for an invalid ISO date."""
    if isinstance(value, np.datetime64):
        value = pd.Timestamp(value).to_pydatetime()
    if isinstance(value, datetime):
        label = "native datetime (timezone)" if value.tzinfo else "native datetime"
        return (value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value), label
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day), "native date"
    if not isinstance(value, str) or not ISO_DATE.fullmatch(value.strip()):
        return None, None
    text = value.strip()
    label = _iso_format(text)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None, label
    if parsed.tzinfo:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed, label


def profile_datetime(series: pd.Series, now: datetime | None = None, examples: int = 5) -> DatetimeSummary | None:
    """Summarize date-like values in a column; None when the column has none."""
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(tzinfo=None)
    parsed: list[datetime] = []
    formats: dict[str, int] = {}
    invalid: list[str] = []
    non_iso: list[str] = []
    future: list[str] = []
    aware = naive = 0
    for value in series.dropna().tolist():
        moment, label = _parse(value)
        if label is None:
            if isinstance(value, str) and NON_ISO_DATE.fullmatch(value.strip()):
                non_iso.append(value)
                formats["non-ISO date text"] = formats.get("non-ISO date text", 0) + 1
            continue
        formats[label] = formats.get(label, 0) + 1
        if moment is None:
            invalid.append(str(value))
            continue
        if "+TZ" in label or label.endswith("Z") or "timezone" in label:
            aware += 1
        else:
            naive += 1
        parsed.append(moment)
        is_date_only = label in {"YYYY-MM-DD", "native date"}
        if (moment.date() > now.date()) if is_date_only else moment > now:
            future.append(str(value))
    if not parsed and not invalid:
        return None
    low, high = (min(parsed), max(parsed)) if parsed else (None, None)
    return DatetimeSummary(
        count=len(parsed), invalid_count=len(invalid), invalid_examples=list(dict.fromkeys(invalid))[:examples],
        minimum=low.isoformat() if low else None, maximum=high.isoformat() if high else None,
        span_days=(high - low).total_seconds() / 86400 if low and high else None,
        future_count=len(future), future_examples=list(dict.fromkeys(future))[:examples],
        reference_time=now.isoformat(timespec="seconds") + "Z", formats=formats,
        timezone_aware_count=aware, naive_count=naive,
        non_iso_count=len(non_iso), non_iso_examples=list(dict.fromkeys(non_iso))[:examples],
    )
