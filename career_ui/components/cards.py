from typing import Any
from html import escape
from nicegui import ui

def metric_card(label: str, value: Any, note: str = "", classes: str = ""):
    """A dense metric card for dashboards."""
    with ui.element("div").classes(f"cw-panel cw-metric {classes}"):
        ui.html(f'<div class="cw-metric-label">{escape(str(label))}</div>')
        ui.html(f'<div class="cw-metric-value">{escape(str(value))}</div>')
        if note:
            ui.html(f'<div class="cw-metric-note">{escape(str(note))}</div>')

def panel(classes: str = ""):
    """A standard border panel."""
    return ui.element("div").classes(f"cw-panel {classes}")

def panel_p(classes: str = ""):
    """A standard border panel with padding."""
    return ui.element("div").classes(f"cw-panel cw-panel-p {classes}")
