import pandas as pd
from nicegui import ui

from career_ui.layouts.page import section_header
from career_ui.components.cards import panel_p, metric_card
from career_ui.tables.data_table import DataTable
from career_ui.widgets.work_queue import work_queue_layout

from career_ui.services.control_center import (
    WORKFLOW_STATUSES,
    get_queue_analytics,
    get_workflow_queue,
    workflow_queue_add_note,
    workflow_queue_retry,
    workflow_queue_transition,
)

@ui.page("/workflow-queue")
def page() -> None:
    def builder():
        with ui.column().classes("w-full h-full gap-4"):
            
            top_panel = ui.row().classes("w-full gap-4 flex-nowrap items-start")
            
            # Action Panel (combining transition/retry/note into a tabbed view)
            with panel_p("w-[300px] flex-shrink-0 flex-col gap-3").classes("bg-[var(--panel)]"):
                section_header("Operations", "Manage queue items")
                
                with ui.tabs().classes('w-full') as tabs:
                    ui.tab('Transition', icon='swap_horiz')
                    ui.tab('Note', icon='note_add')
                    ui.tab('Retry', icon='replay')
                
                with ui.tab_panels(tabs, value='Transition').classes('w-full bg-transparent p-0'):
                    with ui.tab_panel('Transition').classes('p-0 mt-3'):
                        t_job_id = ui.input("Job ID").props("outlined dense").classes("w-full mb-2")
                        t_status = ui.select(WORKFLOW_STATUSES, label="New status").props("outlined dense").classes("w-full mb-2")
                        t_note = ui.input("Note").props("outlined dense").classes("w-full mb-3")
                        def do_transition():
                            if not t_job_id.value or not t_status.value: return ui.notify("Missing fields", type="warning")
                            try:
                                from src.application.workflow import WorkflowStatus
                                if workflow_queue_transition(str(t_job_id.value), WorkflowStatus(t_status.value), actor="user", note=str(t_note.value or "")):
                                    ui.notify("Transition applied", type="positive")
                                    refresh()
                                else: ui.notify("Job ID not found", type="warning")
                            except Exception as e: ui.notify(str(e), type="negative")
                        ui.button("Apply Transition", on_click=do_transition).props("color=primary unelevated").classes("w-full shadow-lg")

                    with ui.tab_panel('Note').classes('p-0 mt-3'):
                        n_job_id = ui.input("Job ID").props("outlined dense").classes("w-full mb-2")
                        n_text = ui.textarea("Note text").props("outlined dense").classes("w-full mb-3")
                        def do_note():
                            if not n_job_id.value or not n_text.value: return ui.notify("Missing fields", type="warning")
                            if workflow_queue_add_note(str(n_job_id.value), str(n_text.value), author="user"):
                                ui.notify("Note added", type="positive")
                            else: ui.notify("Job ID not found", type="warning")
                        ui.button("Add Note", on_click=do_note).props("color=primary unelevated").classes("w-full")

                    with ui.tab_panel('Retry').classes('p-0 mt-3'):
                        r_job_id = ui.input("Job ID").props("outlined dense").classes("w-full mb-3")
                        def do_retry():
                            if not r_job_id.value: return
                            if workflow_queue_retry(str(r_job_id.value)):
                                ui.notify("Retry queued", type="positive")
                                refresh()
                            else: ui.notify("Failed", type="warning")
                        ui.button("Retry Item", on_click=do_retry).props("color=secondary unelevated text-black").classes("w-full")

            # Metrics
            analytics_host = ui.row().classes("flex-grow gap-3 flex-wrap")
            
            table_host = ui.column().classes("w-full flex-grow min-h-0")

            def refresh():
                analytics_host.clear()
                table_host.clear()
                wq = get_workflow_queue()
                analytics = get_queue_analytics(wq)
                funnel = analytics.conversion_funnel()
                
                with analytics_host:
                    for item in funnel:
                        metric_card(item["status"].replace("_", " ").title(), item["count"], f"{item['conversion_rate_pct']}%", classes="w-[120px]")

                items = wq.list(sort_by="updated_at", sort_dir="desc")
                with table_host:
                    if not items:
                        from career_ui.components.feedback import empty_state
                        empty_state("No queue items", "Queue is currently empty.")
                        return
                    display_cols = ["job_id", "title", "company", "workflow_status", "priority", "retry_count", "updated_at"]
                    rows = [{k: row.get(k, "") for k in display_cols} for row in items]
                    DataTable(pd.DataFrame(rows), title="Queue Items", classes="h-full")
            
            with top_panel:
                analytics_host.move()
            
            refresh()
            
    work_queue_layout("/workflow-queue", builder)
