from nicegui import ui

from career_ui.layouts.page import section_header, metrics_grid
from career_ui.components.cards import metric_card, panel_p
from career_ui.tables.data_table import DataTable
from career_ui.widgets.work_queue import work_queue_layout
from career_ui.components.job_drawer import show_job_drawer

from career_ui.services.control_center import read_manual_action_queue, review_cases

@ui.page("/review-queue")
def page():
    def builder():
        with ui.column().classes("w-full h-full gap-4"):
            failures = review_cases()
            external = read_manual_action_queue()

            pending = len(external) if not external.empty else 0
            if not external.empty and "status" in external:
                pending = int(external.status.fillna("").astype(str).str.upper().eq("PENDING").sum())

            total = len(failures) + pending
            state = "CLEAR" if total == 0 else "ACTION"

            with metrics_grid(cols=4):
                metric_card("Review Cases", len(failures), "application failures")
                metric_card("External Actions", pending, "pending manual steps")
                metric_card("Total Exceptions", total, "needs attention")
                metric_card("Queue State", state, "operational state")

            with ui.row().classes("w-full h-full gap-4 flex-nowrap items-stretch min-h-0"):

                with panel_p("flex-[1] min-w-0 flex flex-col gap-2"):
                    section_header("Application failures", "Investigate before retrying")
                    if failures.empty:
                        from career_ui.components.feedback import empty_state
                        empty_state("No application review cases")
                    else:
                        t1 = DataTable(failures, classes="flex-grow h-full")
                        t1.grid.on('rowClicked', lambda e: show_job_drawer(e.args.get('data', {})))

                with panel_p("w-1/2 flex-shrink-0 flex flex-col gap-2 min-h-0"):
                    section_header("Pipeline external actions", "Applications requiring browser-side action")
                    if external.empty:
                        from career_ui.components.feedback import empty_state
                        empty_state("No external actions")
                    else:
                        t2 = DataTable(external, classes="flex-grow h-full")
                        t2.grid.on('rowClicked', lambda e: show_job_drawer(e.args.get('data', {})))

    work_queue_layout("/review-queue", builder)
