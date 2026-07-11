from typing import Any, Mapping, Sequence
from html import escape
from nicegui import ui

def stage_rail(stages: Mapping[str, Any] | Sequence):
    """A horizontal stage progression rail."""
    items = list(stages.items()) if isinstance(stages, Mapping) else list(stages)
    with ui.element("div").classes("w-full bg-[var(--panel)] border border-[var(--border)] rounded-md p-4 overflow-x-auto"):
        with ui.row().classes("w-full justify-between no-wrap gap-4 items-center"):
            for name, state in items:
                s = str(state or "PENDING").upper()
                color = "var(--neutral)"
                if s in {"SUCCESS", "DONE", "COMPLETED", "PASS"}:
                    color = "var(--success)"
                elif s == "RUNNING":
                    color = "var(--warning)"
                elif s in {"FAILED", "FAIL", "ERROR"}:
                    color = "var(--danger)"
                
                with ui.column().classes("items-center gap-2 min-w-[80px]"):
                    ui.html(f'<div style="width:12px;height:12px;border-radius:50%;background:{color};box-shadow:0 0 10px {color}88"></div>')
                    ui.html(f'<div style="font-size:12px;color:var(--text);font-weight:600;white-space:nowrap">{escape(str(name).replace("_"," ").title())}</div>')
                    ui.html(f'<div style="font-size:10px;color:var(--muted);letter-spacing:0.05em">{escape(s)}</div>')
