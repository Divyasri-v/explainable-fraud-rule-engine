import re
from datetime import datetime, timezone


def as_utc(dt: datetime) -> datetime:
    """Treat naive datetimes as UTC so comparisons never mix naive/aware values."""
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def inr(value: float) -> str:
    """Format a number using Indian digit grouping, e.g. 120000 -> ₹1,20,000."""
    s = f"{abs(value):.0f}"
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        s = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head) + "," + tail
    return "₹" + s
