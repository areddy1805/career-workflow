from nicegui import ui

from career_ui.shell import shell
from career_ui.layouts.page import page_header, section_header
from career_ui.components.cards import panel_p
from career_ui.components.badges import status_badge
from career_ui.tables.data_table import DataTable
from career_ui.services.control_center import read_applications

@ui.page("/jobs")
def page():
    shell("/jobs")
    
    with ui.column().classes("w-full max-w-[1600px] mx-auto p-4 gap-4 h-[calc(100vh-60px)]"):
        page_header("Jobs", "Search, filter, and inspect the job portfolio.", kicker="Workspace")
        
        frame = read_applications()
        if frame.empty:
            from career_ui.components.feedback import empty_state
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
                search.on('update:model-value', lambda e: table.grid.run_grid_method('setQuickFilter', e.value))
                
            # Right: Details Inspector
            with panel_p("w-80 flex-shrink-0 flex flex-col gap-4 overflow-y-auto bg-[var(--bg)] border-l border-[var(--border)]"):
                section_header("Inspector", "Select a job to view details")
                
                details_container = ui.column().classes("w-full gap-2")
                with details_container:
                    from career_ui.components.feedback import empty_state
                    empty_state("No selection", "Click a row in the table to inspect.", icon="info")
                    
                def on_row_click(e):
                    details_container.clear()
                    row = e.args.get('data', {})
                    with details_container:
                        ui.html(f'<div class="text-lg font-bold leading-tight" style="color:var(--text)">{row.get("title", "Unknown Title")}</div>')
                        ui.html(f'<div class="text-sm font-medium" style="color:var(--primary)">{row.get("company", "Unknown Company")}</div>')
                        
                        ui.row().classes("w-full h-px bg-[var(--border)] my-2")
                        status_badge(row.get("status", "UNKNOWN"), classes="mb-2")
                        
                        for k, v in row.items():
                            if k not in ("title", "company", "status"):
                                ui.html(f'<div class="text-[10px] font-bold uppercase tracking-wider mt-2" style="color:var(--muted)">{str(k).replace("_", " ")}</div>')
                                ui.html(f'<div class="text-[13px] break-words" style="color:var(--text)">{str(v)}</div>')
                
                table.grid.on('rowClicked', on_row_click)
