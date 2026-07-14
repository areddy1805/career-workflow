from typing import Sequence
from html import escape
from nicegui import ui

def funnel(items: Sequence[tuple[str, int]]):
    """A simple HTML-based horizontal funnel/bar chart."""
    values = [int(v or 0) for _, v in items]
    peak = max([1, *values])
    with ui.element("div").classes("w-full bg-[var(--panel)] border border-[var(--border)] rounded-md p-4 flex flex-col gap-3"):
        for name, value in items:
            v = int(value or 0)
            width = (v / peak * 100) if v else 0
            bg = "var(--primary)" if v else "var(--muted)"

            with ui.row().classes("w-full items-center no-wrap gap-3"):
                ui.html(f'<div style="width:80px;font-size:12px;color:var(--text);font-weight:500;text-align:right">{escape(str(name))}</div>')
                with ui.element("div").classes("flex-grow h-2 bg-[var(--hover)] rounded overflow-hidden"):
                    ui.html(f'<div style="width:{width:.2f}%;height:100%;background:{bg};border-radius:4px;transition:width 0.3s ease"></div>')
                ui.html(f'<div style="width:40px;font-size:12px;color:var(--text);font-weight:600;text-align:right">{v:,}</div>')
