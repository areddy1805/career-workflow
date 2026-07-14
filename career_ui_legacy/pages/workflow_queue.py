import pandas as pd
from nicegui import ui

from career_ui_legacy.layouts.page import section_header
from career_ui_legacy.components.cards import panel_p, metric_card
from career_ui_legacy.tables.data_table import DataTable
from career_ui_legacy.widgets.work_queue import work_queue_layout
from career_ui_legacy.components.job_drawer import show_job_drawer

from career_ui_legacy.services.control_center import (
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

            # Metrics
            analytics_host = ui.row().classes("flex-grow gap-3 flex-wrap w-full")

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
                        from career_ui_legacy.components.feedback import empty_state
                        empty_state("No queue items", "Queue is currently empty.")
                        return
                    display_cols = ["job_id", "title", "company", "workflow_status", "priority", "retry_count", "updated_at"]
                    rows = [{k: row.get(k, "") for k in display_cols} for row in items]
                    # Also need full items mapping for drawer actions, so we attach the original item not just mapped row
                    table = DataTable(pd.DataFrame(rows), title="Queue Items", classes="h-full")

                    # Ensure original items dictionary lookup for drawer
                    item_lookup = {r["job_id"]: r for r in items}
                    table.grid.on('rowClicked', lambda e: show_job_drawer(item_lookup.get(e.args.get('data', {}).get('job_id'), {}), on_change=refresh))

            with top_panel:
                analytics_host.move()

            refresh()

    work_queue_layout("/workflow-queue", builder)
