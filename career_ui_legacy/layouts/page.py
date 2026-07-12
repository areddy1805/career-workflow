from html import escape
from nicegui import ui

def page_header(title: str, subtitle: str = "", kicker: str = "", status: str | None = None):
    """Standard header for primary domain pages."""
    with ui.row().classes("w-full items-start justify-between gap-4 border-b border-[var(--border)] pb-6 mb-6"):
        with ui.column().classes("gap-1"):
            if kicker:
                ui.html(f'<div class="font-mono uppercase" style="color:var(--info);letter-spacing:0.05em;font-size:11px;font-weight:600">{escape(kicker)}</div>')
            ui.html(f'<div class="text-xl font-semibold" style="color:var(--text);letter-spacing:-0.02em">{escape(title)}</div>')
            if subtitle:
                ui.html(f'<div class="text-xs" style="color:var(--muted)">{escape(subtitle)}</div>')

        if status:
            from career_ui.components.badges import status_badge
            status_badge(status)

def section_header(title: str, subtitle: str = ""):
    """Header for sections within a page."""
    ui.html(
        f'<div class="w-full mb-3 mt-4">'
        f'<div style="font-weight:600;font-size:14px;color:var(--text)">{escape(title)}</div>'
        f'<div style="font-size:12px;color:var(--muted)">{escape(subtitle)}</div>'
        f'</div>'
    )

def split_pane():
    """A layout providing a left narrow sidebar and right wide content area."""
    return ui.row().classes("w-full gap-6 flex-nowrap items-start")

def metrics_grid(cols: int = 4, classes: str = ""):
    """A responsive grid specifically for metric cards."""
    return ui.element("div").classes(f"grid grid-cols-{cols} gap-4 w-full {classes}")
