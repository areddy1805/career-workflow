import pandas as pd
from nicegui import ui

from career_ui_legacy.shell import shell
from career_ui_legacy.layouts.page import page_header, section_header
from career_ui_legacy.components.cards import panel_p
from career_ui_legacy.tables.data_table import DataTable
from career_ui_legacy.services.control_center import (
    MANUAL_JOBS_DB,
    ledger_path,
    manual_queue_path,
    runs_path,
    safe_settings,
)

@ui.page("/settings")
def page():
    shell("/settings")
    with ui.column().classes("w-full max-w-[1600px] mx-auto p-4 gap-6 pb-20"):
        page_header("Settings", "Read-only operational configuration and resolved storage paths.", kicker="System", status="READ ONLY")

        with ui.row().classes("w-full gap-6 flex-nowrap items-stretch"):
            with panel_p("w-1/2 flex flex-col gap-2"):
                section_header("Operational Configuration", "Safe non-secret environment values")
                DataTable(pd.DataFrame([{"Setting": k, "Value": v or "DEFAULT / NOT SET"} for k, v in safe_settings().items()]), classes="flex-grow min-h-[300px]")

            with panel_p("w-1/2 flex flex-col gap-2"):
                section_header("Storage", "Resolved local persistence paths")
                paths = [
                    ("Application Ledger", ledger_path()),
                    ("Run Artifacts", runs_path()),
                    ("Pipeline External Queue", manual_queue_path()),
                    ("Manual External Jobs", MANUAL_JOBS_DB),
                ]
                DataTable(pd.DataFrame([{"Store": n, "Path": str(p), "Exists": "YES" if p.exists() else "NO"} for n, p in paths]), classes="flex-grow min-h-[300px]")

        ui.html('<div class="text-[11px] text-[var(--muted)] opacity-70 w-full text-center mt-4 uppercase tracking-wider font-bold">Secret configuration is intentionally excluded from this interface.</div>')
