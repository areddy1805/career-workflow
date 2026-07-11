from nicegui import ui

from career_ui.components import (
    dataframe_table,
    empty_state,
    metric_card,
    page_header,
    section,
)
from career_ui.services.control_center import read_manual_action_queue, review_cases
from career_ui.shell import shell


@ui.page("/review-queue")
def page():
    shell("/review-queue")
    with ui.column().classes("cw-content gap-5"):
        page_header(
            "WORK QUEUE",
            "Review Queue",
            "Failures, manual-review cases, and pending external actions.",
        )
        failures = review_cases()
        external = read_manual_action_queue()
        pending = len(external) if not external.empty else 0
        if not external.empty and "status" in external:
            pending = int(
                external.status.fillna("").astype(str).str.upper().eq("PENDING").sum()
            )
        with ui.element("div").classes("cw-grid-4 w-full"):
            metric_card("Review Cases", len(failures), "application failures")
            metric_card("External Actions", pending, "pending")
            metric_card("Total Exceptions", len(failures) + pending, "needs attention")
            metric_card(
                "Queue State",
                "CLEAR" if len(failures) + pending == 0 else "ACTION",
                "operational",
            )
        section("Application failures and manual review", "Investigate before retrying")
        (
            dataframe_table(failures, pagination=20)
            if not failures.empty
            else empty_state("No application review cases")
        )
        section(
            "Pipeline external actions", "Applications requiring browser-side action"
        )
        (
            dataframe_table(external, pagination=20)
            if not external.empty
            else empty_state("No external actions")
        )
