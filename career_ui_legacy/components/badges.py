from html import escape
from nicegui import ui

def badge(text: str, color: str = "neutral", classes: str = ""):
    """
    Renders a dense, monospaced badge.
    Colors: success, warning, danger, info, neutral.
    """
    valid_colors = {"success", "warning", "danger", "info", "neutral"}
    c = color if color in valid_colors else "neutral"
    ui.html(f'<span class="cw-badge cw-badge-{c} {classes}">{escape(str(text))}</span>')

def status_badge(status: str, classes: str = ""):
    s = str(status or "UNKNOWN").upper()
    color = "neutral"
    if s in {"SUCCESS", "PASS", "ONLINE", "IDLE", "HEALTHY", "COMPLETED", "APPLIED", "READY", "CLEAR", "DONE"}:
        color = "success"
    elif s in {"RUNNING", "PARTIAL", "ORPHANED", "PENDING", "EXECUTION", "DEGRADED", "WARN", "WARNING", "CHECK", "ACTION", "IN_PROGRESS", "TO_APPLY", "SHORTLISTED"}:
        color = "warning"
    elif s in {"FAILED", "FAIL", "ERROR", "UNHEALTHY", "BLOCKED", "REJECTED"}:
        color = "danger"
    elif s in {"SKIPPED", "EXPIRED", "ARCHIVED"}:
        color = "neutral"

    badge(s, color, classes)
