import pandas as pd
from nicegui import ui

from career_ui.components import (
    dataframe_table,
    empty_state,
    metric_card,
    page_header,
    section,
)
from career_ui.services.control_center import (
    WORKFLOW_STATUSES,
    get_queue_analytics,
    get_workflow_queue,
    workflow_queue_add_note,
    workflow_queue_retry,
    workflow_queue_transition,
)
from career_ui.shell import shell


@ui.page("/workflow-queue")
def page() -> None:
    shell("/workflow-queue")
    with ui.column().classes("cw-content gap-5"):
        page_header(
            "WORK QUEUE",
            "Workflow Queue",
            "Full 9-state application lifecycle — from discovery through offer or archive.",
        )

        analytics_host = ui.element("div").classes("cw-grid-5 w-full")
        table_host = ui.column().classes("w-full gap-3")
        detail_host = ui.column().classes("w-full gap-3")

        def refresh(selected_status: str | None = None, search_text: str = "") -> None:
            analytics_host.clear()
            table_host.clear()
            detail_host.clear()

            wq = get_workflow_queue()
            analytics = get_queue_analytics(wq)
            dist = analytics.status_distribution()
            funnel = analytics.conversion_funnel()

            with analytics_host:
                for item in funnel:
                    metric_card(
                        item["status"].replace("_", " "),
                        item["count"],
                        f"{item['conversion_rate_pct']}% of total",
                    )

            items = wq.list(
                status=selected_status,
                search=search_text or None,
                sort_by="updated_at",
                sort_dir="desc",
            )

            with table_host:
                if not items:
                    empty_state(
                        "No queue items",
                        "Add jobs via the pipeline or Manual Queue page.",
                    )
                    return

                display_cols = [
                    "job_id",
                    "title",
                    "company",
                    "workflow_status",
                    "priority",
                    "retry_count",
                    "updated_at",
                ]
                rows = [{k: row.get(k, "") for k in display_cols} for row in items]
                frame = pd.DataFrame(rows)
                dataframe_table(frame, pagination=25)

        # ── Controls ──────────────────────────────────────────────────
        with ui.row().classes("items-end gap-3 flex-wrap w-full"):
            status_filter = (
                ui.select(
                    ["ALL"] + WORKFLOW_STATUSES,
                    label="Filter by status",
                    value="ALL",
                )
                .props("outlined dense")
                .classes("w-48")
            )
            search_box = (
                ui.input(placeholder="Search title / company…")
                .props("outlined dense")
                .classes("w-64")
            )
            ui.button(
                "Apply",
                icon="filter_list",
                on_click=lambda: refresh(
                    None if status_filter.value == "ALL" else status_filter.value,
                    search_box.value,
                ),
            ).props("outline")

        section("Queue items", "Sorted by most recently updated")
        refresh()

        # ── Manual transition panel ───────────────────────────────────
        with ui.expansion("Manually transition an item", icon="swap_horiz").classes(
            "cw-card w-full"
        ):
            with ui.grid(columns=2).classes("w-full gap-3 p-3"):
                t_job_id = ui.input("Job ID").props("outlined dense")
                t_status = ui.select(WORKFLOW_STATUSES, label="New status").props(
                    "outlined dense"
                )
                t_actor = ui.input("Actor", value="user").props("outlined dense")
                t_note = ui.input("Note").props("outlined dense")

            def do_transition() -> None:
                if not t_job_id.value or not t_status.value:
                    ui.notify("Job ID and status are required", type="warning")
                    return
                try:
                    from src.application.workflow import WorkflowStatus

                    ok = workflow_queue_transition(
                        str(t_job_id.value),
                        WorkflowStatus(t_status.value),
                        actor=str(t_actor.value or "user"),
                        note=str(t_note.value or ""),
                    )
                    if ok:
                        ui.notify("Transition applied", type="positive")
                        refresh()
                    else:
                        ui.notify("Job ID not found in queue", type="warning")
                except Exception as exc:
                    ui.notify(str(exc), type="negative")

            ui.button("Apply Transition", on_click=do_transition).props(
                "color=primary unelevated"
            ).classes("m-3")

        # ── Add note panel ────────────────────────────────────────────
        with ui.expansion("Add a note", icon="note_add").classes("cw-card w-full"):
            with ui.grid(columns=2).classes("w-full gap-3 p-3"):
                n_job_id = ui.input("Job ID").props("outlined dense")
                n_author = ui.input("Author", value="user").props("outlined dense")
                n_text = (
                    ui.textarea("Note text").classes("col-span-2").props("outlined")
                )

            def do_note() -> None:
                if not n_job_id.value or not n_text.value:
                    ui.notify("Job ID and note text are required", type="warning")
                    return
                ok = workflow_queue_add_note(
                    str(n_job_id.value),
                    str(n_text.value),
                    author=str(n_author.value or "user"),
                )
                if ok:
                    ui.notify("Note added", type="positive")
                else:
                    ui.notify("Job ID not found", type="warning")

            ui.button("Add Note", on_click=do_note).props(
                "color=primary unelevated"
            ).classes("m-3")

        # ── Retry panel ───────────────────────────────────────────────
        with ui.expansion("Retry a failed item", icon="replay").classes(
            "cw-card w-full"
        ):
            r_job_id = ui.input("Job ID").props("outlined dense").classes("m-3 w-64")

            def do_retry() -> None:
                if not r_job_id.value:
                    ui.notify("Job ID is required", type="warning")
                    return
                ok = workflow_queue_retry(str(r_job_id.value))
                if ok:
                    ui.notify("Retry queued", type="positive")
                    refresh()
                else:
                    ui.notify(
                        "Cannot retry: item not found or max retries exceeded",
                        type="warning",
                    )

            ui.button("Retry", on_click=do_retry).props(
                "color=secondary unelevated"
            ).classes("m-3")
