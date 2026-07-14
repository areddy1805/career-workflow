from nicegui import ui

from career_ui_legacy.layouts.page import section_header, metrics_grid
from career_ui_legacy.components.cards import metric_card, panel_p
from career_ui_legacy.tables.data_table import DataTable
from career_ui_legacy.widgets.work_queue import work_queue_layout
from career_ui_legacy.components.job_drawer import show_job_drawer

from career_ui_legacy.services.control_center import latest_terminal_run
from control_center.run_inspector import read_json_artifact
import pandas as pd

@ui.page("/review-queue")
def page():
    def builder():
        with ui.column().classes("w-full h-full gap-4"):
            run_id = latest_terminal_run()
            if not run_id:
                from career_ui_legacy.components.feedback import empty_state
                empty_state("No runs available")
                return

            jobs = read_json_artifact(run_id, "selected_jobs.json") or []
            df = pd.DataFrame(jobs)

            with metrics_grid(cols=2):
                metric_card("Selected Jobs", len(df), "for review")
                metric_card("Queue State", "ACTION" if not df.empty else "CLEAR", "operational state")

            with ui.row().classes("w-full h-full gap-4 flex-nowrap items-stretch min-h-0"):
                with panel_p("flex-[1] min-w-0 flex flex-col gap-2"):
                    section_header("Review Queue", "Jobs selected for application")
                    if df.empty:
                        from career_ui_legacy.components.feedback import empty_state
                        empty_state("No selected jobs in latest run")
                    else:
                        display = [c for c in ("job_id", "title", "company", "score", "subtrack", "priority") if c in df.columns]
                        t1 = DataTable(df[display] if display else df, classes="flex-grow h-full")
                        t1.grid.on('rowClicked', lambda e: show_job_drawer(e.args.get('data', {})))

    work_queue_layout("/review-queue", builder)
