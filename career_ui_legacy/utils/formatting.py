from datetime import datetime, timezone
import dateutil.parser
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def format_datetime(iso_string: str | None) -> str:
    """Format an ISO 8601 string to IST timezone (e.g. 'Oct 12, 14:30 IST')."""
    if not iso_string:
        return "N/A"
    try:
        dt = dateutil.parser.isoparse(iso_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ist_dt = dt.astimezone(IST)
        return ist_dt.strftime("%b %d, %H:%M IST")
    except Exception:
        return str(iso_string)

def format_duration(ms: int | float | None) -> str:
    """Format duration in milliseconds to a human-readable string."""
    if ms is None:
        return "0s"

    seconds = ms / 1000.0
    if seconds < 1:
        return f"{int(ms)}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    hours = int(minutes // 60)
    minutes = int(minutes % 60)
    return f"{hours}h {minutes}m"

def format_relative_time(iso_string: str | None) -> str:
    """Format an ISO string to a relative time ('2 hours ago')."""
    if not iso_string:
        return "N/A"
    try:
        dt = dateutil.parser.isoparse(iso_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - dt

        seconds = diff.total_seconds()

        if seconds < 60:
            return "just now"
        if seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        if seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"

        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    except Exception:
        return str(iso_string)
