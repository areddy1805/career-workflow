import json
import pandas as pd
from nicegui import ui

from career_ui.shell import shell
from career_ui.layouts.page import page_header, section_header, split_pane
from career_ui.components.cards import panel_p
from career_ui.tables.data_table import DataTable
from career_ui.services.control_center import available_runs, inspect_run

@ui.page("/runs")
def page():
    shell("/runs")
    with ui.column().classes("w-full max-w-[1600px] mx-auto p-4 gap-6 pb-20 h-[calc(100vh-60px)]"):
        page_header("Run Inspector", "Inspect immutable run state, result payloads, and generated artifacts.", kicker="Inspect")
        
        runs = available_runs()
        if not runs:
            from career_ui.components.feedback import empty_state
            empty_state("No run artifacts available")
            return
            
        with split_pane():
            with panel_p("w-[30%] min-w-[300px] flex-shrink-0 flex flex-col gap-4 h-full"):
                section_header("Run Selection", "Select an artifact to inspect")
                select = ui.select(runs, label="Run ID", value=runs[0]).props("outlined dense").classes("w-full")
                ui.html('<div class="text-[12px] text-[var(--muted)]">Artifacts are immutable representations of execution state.</div>')
                
            with ui.column().classes("flex-grow h-full min-w-0"):
                host = ui.column().classes("w-full h-full gap-4")

                def render():
                    host.clear()
                    payload = inspect_run(select.value)
                    with host:
                        with ui.tabs().classes("w-full") as tabs:
                            a = ui.tab("State")
                            b = ui.tab("Result")
                            c = ui.tab("Artifacts")
                            
                        with ui.tab_panels(tabs, value=a).classes("w-full h-full min-h-[500px] bg-transparent p-0"):
                            with ui.tab_panel(a).classes("p-0 h-full"):
                                with panel_p("w-full h-full flex flex-col"):
                                    ui.code(json.dumps(payload.get("state", {}), indent=2), language="json").classes("w-full h-full bg-[var(--bg)] border border-[var(--border)] rounded overflow-y-auto text-[13px]")
                                    
                            with ui.tab_panel(b).classes("p-0 h-full"):
                                with panel_p("w-full h-full flex flex-col"):
                                    ui.code(json.dumps(payload.get("result", {}), indent=2), language="json").classes("w-full h-full bg-[var(--bg)] border border-[var(--border)] rounded overflow-y-auto text-[13px]")
                                    
                            with ui.tab_panel(c).classes("p-0 h-full"):
                                with panel_p("w-full h-full flex flex-col gap-2"):
                                    files = payload.get("files", [])
                                    if files:
                                        DataTable(pd.DataFrame(files), classes="w-full h-full min-h-[400px] flex-grow")
                                    else:
                                        from career_ui.components.feedback import empty_state
                                        empty_state("No artifacts generated in this run")

                select.on_value_change(lambda _: render())
                render()
