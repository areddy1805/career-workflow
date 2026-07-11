from nicegui import ui

from career_ui.components import (
    dataframe_table,
    empty_state,
    metric_card,
    page_header,
)
from career_ui.services.control_center import (
    application_summary,
    read_applications,
    run_reconciliation,
)
from career_ui.shell import shell


@ui.page("/applications")
def page():
    shell("/applications")
    with ui.column().classes("cw-content gap-5"):
        page_header(
            "WORKSPACE",
            "Applications",
            "Execution state, recruiting lifecycle, and reconciliation.",
        )
        s = application_summary()
        with ui.element("div").classes("cw-grid-4 w-full"):
            metric_card("Total", s.get("total", 0), "ledger")
            metric_card("Viewed", s.get("viewed", 0), "response signal")
            metric_card("Interview", s.get("interview", 0), "active funnel")
            metric_card("Offer", s.get("offer", 0), "conversion")

        async def reconcile():
            ui.notify("Reconciliation started")
            result = await ui.run.io_bound(run_reconciliation)
            ui.notify(
                (
                    "Reconciliation complete"
                    if result.ok
                    else f"Failed: {result.returncode}"
                ),
                type="positive" if result.ok else "negative",
            )

        ui.button("Run Reconciliation", icon="sync", on_click=reconcile).props(
            "color=primary unelevated"
        )
        frame = read_applications()
        if frame.empty:
            empty_state("No applications in ledger")
            return
        search = (
            ui.input(placeholder="Search applications…")
            .props("outlined dense clearable")
            .classes("w-full max-w-xl")
        )
        host = ui.column().classes("w-full")

        def render():
            host.clear()
            f = frame
            q = (search.value or "").lower().strip()
            if q:
                cols = [
                    c
                    for c in (
                        "title",
                        "company",
                        "location",
                        "lifecycle_stage",
                        "priority",
                    )
                    if c in f.columns
                ]
                mask = (
                    f[cols]
                    .fillna("")
                    .astype(str)
                    .apply(
                        lambda r: r.str.lower().str.contains(q, regex=False).any(),
                        axis=1,
                    )
                )
                f = f[mask]
            display = [
                c
                for c in (
                    "job_id",
                    "title",
                    "company",
                    "score",
                    "priority",
                    "subtrack",
                    "status",
                    "lifecycle_stage",
                    "applied_at",
                )
                if c in f.columns
            ]
            with host:
                dataframe_table(f[display], pagination=25)

        search.on_value_change(lambda _: render())
        render()
