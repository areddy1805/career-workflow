from nicegui import ui

from career_ui.layouts.page import section_header, metrics_grid
from career_ui.components.cards import panel_p, metric_card
from career_ui.tables.data_table import DataTable
from career_ui.widgets.work_queue import work_queue_layout
from career_ui.components.job_drawer import show_job_drawer

from career_ui.services.control_center import (
    MANUAL_JOB_SOURCES,
    add_manual_job,
    read_manual_jobs,
    update_external_action_status,
    update_manual_job_status,
    latest_terminal_run
)
from control_center.run_inspector import read_json_artifact
import pandas as pd

@ui.page("/manual-queue")
def page():
    def builder():
        with ui.column().classes("w-full h-full gap-4"):
            with ui.tabs().classes('w-full') as tabs:
                ui.tab('Auto Detected', icon='auto_awesome')
                ui.tab('Manually Sourced', icon='person_add')

            with ui.tab_panels(tabs, value='Auto Detected').classes('w-full flex-grow min-h-0 bg-transparent p-0'):

                with ui.tab_panel('Auto Detected').classes('p-0 h-full flex flex-col gap-4'):
                    auto_host = ui.column().classes("w-full h-full flex-grow min-h-0 gap-4")

                    def refresh_auto():
                        auto_host.clear()
                        run_id = latest_terminal_run()
                        if run_id:
                            manual = read_json_artifact(run_id, "manual_review.json") or []
                            external = read_json_artifact(run_id, "external_apply.json") or []
                            frame = pd.DataFrame(manual + external)
                        else:
                            frame = pd.DataFrame()

                        with auto_host:
                            pending = len(frame) if not frame.empty else 0
                            applied = 0

                            with metrics_grid(cols=4):
                                metric_card("Total", len(frame), "detected")
                                metric_card("Pending", pending, "requires action")
                                metric_card("Applied", applied, "completed externally")
                                metric_card("Remaining", max(0, len(frame) - applied), "open lifecycle")

                            if frame.empty:
                                from career_ui.components.feedback import empty_state
                                empty_state("No external-apply jobs detected")
                            else:
                                display = [c for c in ("job_id", "title", "company", "score", "status", "run_id", "updated_at") if c in frame.columns]
                                table = DataTable(frame[display], title="External applications", classes="flex-grow min-h-[300px]")
                                table.grid.on('rowClicked', lambda e: show_job_drawer(e.args.get('data', {}), on_change=refresh_auto))
                    refresh_auto()

                with ui.tab_panel('Manually Sourced').classes('p-0 h-full flex flex-col gap-4'):

                    with ui.expansion("Add manually sourced opportunity", icon="add_circle").classes("w-full bg-[var(--panel)] border border-[var(--border)] rounded"):
                        with ui.grid(columns=2).classes("w-full gap-3 p-4"):
                            title = ui.input("Title").props("outlined dense")
                            company = ui.input("Company").props("outlined dense")
                            location = ui.input("Location").props("outlined dense")
                            source = ui.select(list(MANUAL_JOB_SOURCES), label="Source", value="LinkedIn").props("outlined dense")
                            url = ui.input("Source URL").props("outlined dense")
                            priority = ui.select(["P1", "P2", "P3"], label="Priority", value="P2").props("outlined dense")
                            notes = ui.textarea("Notes").classes("col-span-2").props("outlined dense")

                            def add():
                                try:
                                    add_manual_job(
                                        title=title.value or "", company=company.value or "",
                                        location=location.value or "", source=source.value,
                                        source_url=url.value or "", priority=priority.value,
                                        notes=notes.value or ""
                                    )
                                    ui.notify("Job added", type="positive")
                                    refresh_manual()
                                except Exception as exc: ui.notify(str(exc), type="negative")

                            ui.button("Save Job", on_click=add).props("color=primary unelevated").classes("col-span-2")

                    manual_host = ui.column().classes("w-full h-full flex-grow min-h-0 gap-4")
                    def refresh_manual():
                        manual_host.clear()
                        frame = read_manual_jobs()
                        with manual_host:
                            if frame.empty:
                                from career_ui.components.feedback import empty_state
                                empty_state("Manual opportunity list is empty")
                            else:
                                display = [c for c in ("id", "title", "company", "location", "source", "status", "priority", "updated_at") if c in frame.columns]
                                table = DataTable(frame[display], title="Manually Sourced", classes="flex-grow min-h-[300px]")
                                table.grid.on('rowClicked', lambda e: show_job_drawer(e.args.get('data', {}), on_change=refresh_manual))
                    refresh_manual()

    work_queue_layout("/manual-queue", builder)
