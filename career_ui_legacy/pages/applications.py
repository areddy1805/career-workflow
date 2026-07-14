from nicegui import ui

from career_ui.layouts.page import section_header, metrics_grid
from career_ui.components.cards import metric_card, panel_p
from career_ui.tables.data_table import DataTable
from career_ui.widgets.work_queue import work_queue_layout

from career_ui.services.control_center import (
    application_summary,
    read_applications,
    run_reconciliation,
)

@ui.page("/applications")
def page():
    def builder():
        with ui.column().classes("w-full h-full gap-4"):
            s = application_summary()

            with ui.row().classes("w-full items-stretch justify-between gap-4 flex-nowrap"):
                metrics_grid_ui = metrics_grid(cols=4, classes="flex-grow min-w-0")
                with metrics_grid_ui:
                    metric_card("Total", s.get("total", 0), "ledger")
                    metric_card("Viewed", s.get("viewed", 0), "response signal")
                    metric_card("Interview", s.get("interview", 0), "active funnel")
                    metric_card("Offer", s.get("offer", 0), "conversion")

                async def reconcile():
                    ui.notify("Reconciliation started")
                    result = await ui.run.io_bound(run_reconciliation)
                    ui.notify("Reconciliation complete" if result.ok else f"Failed: {result.returncode}", type="positive" if result.ok else "negative")

                with panel_p("bg-[var(--panel)] flex-shrink-0 flex items-center justify-center"):
                    ui.button("Reconcile Emails", icon="sync", on_click=reconcile).props("color=primary unelevated").classes("h-full min-h-[48px] shadow-lg")

            with panel_p("w-full flex-grow min-h-0 flex flex-col gap-2"):
                section_header("Ledger", "Immutable application log")
                frame = read_applications()
                if frame.empty:
                    from career_ui.components.feedback import empty_state
                    empty_state("No applications in ledger")
                else:
                    display = [c for c in ("job_id", "title", "company", "score", "priority", "subtrack", "status", "lifecycle_stage", "applied_at") if c in frame.columns]
                    DataTable(frame[display], classes="flex-grow h-full min-h-[400px]")

    work_queue_layout("/applications", builder)
