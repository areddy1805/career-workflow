from nicegui import ui

from career_ui.components import (
    dataframe_table,
    empty_state,
    metric_card,
    page_header,
    section,
)
from career_ui.services.control_center import (
    MANUAL_JOB_SOURCES,
    add_manual_job,
    read_manual_action_queue,
    read_manual_jobs,
    update_external_action_status,
    update_manual_job_status,
)
from career_ui.shell import shell


@ui.page("/manual-queue")
def page():
    shell("/manual-queue")
    with ui.column().classes("cw-content gap-5"):
        page_header(
            "WORK QUEUE",
            "External Apply Queue",
            "Pipeline-detected external applications and manually sourced opportunities in one operational workspace.",
        )
        auto_host = ui.column().classes("w-full gap-4")
        manual_host = ui.column().classes("w-full gap-4")

        def refresh_auto():
            auto_host.clear()
            frame = read_manual_action_queue()
            with auto_host:
                section(
                    "Pipeline-detected external applications",
                    "Jobs the pipeline cannot submit directly",
                )
                pending = (
                    int((frame.status == "PENDING").sum())
                    if not frame.empty and "status" in frame
                    else 0
                )
                applied = (
                    int((frame.status == "APPLIED").sum())
                    if not frame.empty and "status" in frame
                    else 0
                )
                with ui.element("div").classes("cw-grid-4 w-full"):
                    metric_card("Total", len(frame), "detected")
                    metric_card("Pending", pending, "requires action")
                    metric_card("Applied", applied, "completed externally")
                    metric_card(
                        "Remaining", max(0, len(frame) - applied), "open lifecycle"
                    )
                if frame.empty:
                    empty_state("No external-apply jobs detected")
                else:
                    display = [
                        c
                        for c in (
                            "job_id",
                            "title",
                            "company",
                            "score",
                            "status",
                            "run_id",
                            "updated_at",
                        )
                        if c in frame.columns
                    ]
                    dataframe_table(frame[display], pagination=20)
                    with ui.row().classes("items-end gap-3"):
                        jid = ui.input("Job ID").props("outlined dense")
                        status = ui.select(
                            ["PENDING", "IN_PROGRESS", "APPLIED", "SKIPPED", "EXPIRED"],
                            label="Move to",
                        ).props("outlined dense")
                        note = ui.input("Note").props("outlined dense")

                        def move_external():
                            if not jid.value or not status.value:
                                return
                            ok = update_external_action_status(
                                str(jid.value), status.value, note.value or ""
                            )
                            ui.notify(
                                "Status updated" if ok else "Job ID not found",
                                type="positive" if ok else "warning",
                            )
                            refresh_auto()

                        ui.button("Update External Job", on_click=move_external).props(
                            "color=primary unelevated"
                        )

        def refresh_manual():
            manual_host.clear()
            frame = read_manual_jobs()
            with manual_host:
                section(
                    "Manually sourced opportunities",
                    "LinkedIn, referrals, company careers, and other sources",
                )
                if frame.empty:
                    empty_state("Manual opportunity list is empty")
                else:
                    display = [
                        c
                        for c in (
                            "id",
                            "title",
                            "company",
                            "location",
                            "source",
                            "status",
                            "priority",
                            "updated_at",
                        )
                        if c in frame.columns
                    ]
                    dataframe_table(frame[display], pagination=20)
                    with ui.row().classes("items-end gap-3"):
                        jid = ui.number("Job ID", min=1).props("outlined dense")
                        status = ui.select(
                            [
                                "SHORTLISTED",
                                "TO_APPLY",
                                "APPLIED",
                                "SKIPPED",
                                "EXPIRED",
                            ],
                            label="Move to",
                        ).props("outlined dense")

                        def move_manual():
                            if not jid.value or not status.value:
                                return
                            update_manual_job_status(int(jid.value), status.value)
                            ui.notify("Status updated", type="positive")
                            refresh_manual()

                        ui.button("Update Manual Job", on_click=move_manual).props(
                            "color=primary unelevated"
                        )

        with ui.expansion(
            "Add manually sourced opportunity", icon="add_circle"
        ).classes("cw-card w-full"):
            with ui.grid(columns=2).classes("w-full gap-3 p-3"):
                title = ui.input("Title")
                company = ui.input("Company")
                location = ui.input("Location")
                source = ui.select(
                    list(MANUAL_JOB_SOURCES), label="Source", value="LinkedIn"
                )
                url = ui.input("Source URL")
                priority = ui.select(["P1", "P2", "P3"], label="Priority", value="P2")
                notes = ui.textarea("Notes").classes("col-span-2")

            def add():
                try:
                    add_manual_job(
                        title=title.value or "",
                        company=company.value or "",
                        location=location.value or "",
                        source=source.value,
                        source_url=url.value or "",
                        priority=priority.value,
                        notes=notes.value or "",
                    )
                    ui.notify("Job added", type="positive")
                    refresh_manual()
                except Exception as exc:
                    ui.notify(str(exc), type="negative")

            ui.button("Add Job", on_click=add).props(
                "color=primary unelevated"
            ).classes("m-3")

        refresh_auto()
        refresh_manual()
