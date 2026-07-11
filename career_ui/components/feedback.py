from html import escape
from nicegui import ui

def empty_state(title: str, body: str = "", icon: str = "◇", classes: str = ""):
    """Professional empty state indicator."""
    ui.html(
        f'<div class="cw-empty {classes}">'
        f'<div style="font-size:24px;color:var(--muted);margin-bottom:12px">{escape(icon)}</div>'
        f'<div style="color:var(--text);font-weight:600;font-size:14px">{escape(title)}</div>'
        f'<div style="color:var(--muted);font-size:12px;margin-top:4px">{escape(body)}</div>'
        f'</div>'
    )

def callout(title: str, body: str, type: str = "warning", classes: str = ""):
    """Inline informational or warning callout."""
    # types: warning, info, danger
    border_color = f"var(--{type})"
    ui.html(
        f'<div class="cw-panel cw-panel-p {classes}" style="border-left: 3px solid {border_color}">'
        f'<div style="font-weight:600;font-size:13px;margin-bottom:4px;color:var(--text)">{escape(title)}</div>'
        f'<div style="color:var(--muted);font-size:12px">{escape(body)}</div>'
        f'</div>'
    )
