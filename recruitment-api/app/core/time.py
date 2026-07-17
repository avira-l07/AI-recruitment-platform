from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return a naive UTC datetime for compatibility with existing DB columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
