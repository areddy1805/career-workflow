import html
from nicegui import ui

from career_ui_legacy.shell import shell
from career_ui_legacy.layouts.page import page_header, section_header
from career_ui_legacy.components.cards import panel_p
from career_ui_legacy.components.badges import status_badge
from career_ui_legacy.tables.data_table import DataTable
from career_ui_legacy.services.control_center import read_applications
from career_ui_legacy.components.job_drawer import show_job_drawer

@ui.page("/jobs")
def page():
    shell("/jobs")

    with ui.column().classes("w-full max-w-[1600px] mx-auto p-4 gap-4 h-[calc(100vh-60px)]"):
        page_header("Jobs", "Search, filter, and inspect the job portfolio.", kicker="Workspace")

        frame = read_applications()
        if frame.empty:
            from career_ui_legacy.components.feedback import empty_state
            empty_state("No job records available", "Run acquisition or import jobs first.", classes="mt-10")
            return

        display = [c for c in ("job_id", "title", "company", "location", "score", "priority", "subtrack", "source", "status") if c in frame.columns]

        # IDE Split Layout
        with ui.row().classes("w-full h-[70vh] gap-4 flex-nowrap items-stretch"):

            # Left: Filters
            with panel_p("w-64 flex-shrink-0 flex flex-col gap-4 overflow-y-auto"):
                section_header("Filters")
                search = ui.input("Search").props('dense outlined clearable').classes('w-full text-sm')
                ui.select(["ALL", "ACTIVE", "ARCHIVED"], label="State", value="ALL").props('dense outlined').classes('w-full')
                ui.select(["ALL", "P0", "P1", "P2"], label="Priority", value="ALL").props('dense outlined').classes('w-full')
                ui.html('<div class="text-xs text-[var(--muted)] mt-4">Advanced filtering is currently disabled. Use the quick search above.</div>')

            # Middle: Table
            with ui.column().classes("flex-grow min-w-0 h-full overflow-hidden"):
                table = DataTable(frame[display], classes="h-full")
                # Bind search filter to table quick filter
                search.on('update:model-value', lambda e: table.grid.run_grid_method('setQuickFilter', e.value or ''))

                # Bind universal job drawer
                table.grid.on('rowClicked', lambda e: show_job_drawer(e.args.get('data', {})))
