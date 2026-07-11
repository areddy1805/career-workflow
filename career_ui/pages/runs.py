import json

from nicegui import ui

from career_ui.components import dataframe_table, empty_state, page_header
from career_ui.services.control_center import (
    available_runs,
    inspect_run,
)
from career_ui.shell import shell


@ui.page("/runs")
def page():
    shell("/runs")
    with ui.column().classes("cw-content gap-5"):
        page_header(
            "INSPECT",
            "Run Inspector",
            "Inspect immutable run state, result payloads, and generated artifacts.",
        )
        runs = available_runs()
        if not runs:
            empty_state("No run artifacts available")
            return
        select = (
            ui.select(runs, label="Run", value=runs[0])
            .props("outlined dense")
            .classes("w-full max-w-xl")
        )
        host = ui.column().classes("w-full gap-4")

        def render():
            host.clear()
            payload = inspect_run(select.value)
            with host:
                with ui.tabs().classes("w-full") as tabs:
                    a = ui.tab("State")
                    b = ui.tab("Result")
                    c = ui.tab("Artifacts")
                with ui.tab_panels(tabs, value=a).classes("w-full bg-transparent"):
                    with ui.tab_panel(a):
                        ui.code(
                            json.dumps(payload.get("state", {}), indent=2),
                            language="json",
                        ).classes("w-full")
                    with ui.tab_panel(b):
                        ui.code(
                            json.dumps(payload.get("result", {}), indent=2),
                            language="json",
                        ).classes("w-full")
                    with ui.tab_panel(c):
                        import pandas as pd

                        files = payload.get("files", [])
                        (
                            dataframe_table(pd.DataFrame(files))
                            if files
                            else empty_state("No artifacts")
                        )

        select.on_value_change(lambda _: render())
        render()
