import json
import pandas as pd
from nicegui import ui

from career_ui.shell import shell
from career_ui.layouts.page import page_header, section_header, split_pane
from career_ui.components.cards import panel_p
from career_ui.tables.data_table import DataTable
from career_ui.services.control_center import available_runs, inspect_run
from control_center.run_inspector import read_json_artifact, read_text_artifact
from career_ui.utils.formatting import format_datetime, format_duration

@ui.page("/runs")
def page():
    shell("/runs")
    with ui.column().classes("w-full max-w-[1600px] mx-auto p-4 gap-6 pb-20 h-[calc(100vh-60px)]"):
        page_header("Run Inspector", "Inspect immutable run state, result payloads, and generated artifacts.", kicker="Inspect")
        
        runs = available_runs()
        if not runs:
            from career_ui.components.feedback import empty_state
            empty_state("No run artifacts available")
            return
            
        with split_pane():
            with panel_p("w-[30%] min-w-[300px] flex-shrink-0 flex flex-col gap-4 h-full"):
                section_header("Run Selection", "Select an artifact to inspect")
                select = ui.select(runs, label="Run ID", value=runs[0]).props("outlined dense").classes("w-full")
                ui.html('<div class="text-[12px] text-[var(--muted)]">Artifacts are immutable representations of execution state.</div>')
                
            with ui.column().classes("flex-grow h-full min-w-0"):
                host = ui.column().classes("w-full h-full gap-4")

                def render():
                    host.clear()
                    run_id = select.value
                    payload = inspect_run(run_id)
                    
                    manifest = read_json_artifact(run_id, "manifest.json")
                    timeline = read_json_artifact(run_id, "timeline.json")
                    environment = read_json_artifact(run_id, "environment.json")
                    diagnostics = read_json_artifact(run_id, "diagnostics.json")
                    
                    classification = read_json_artifact(run_id, "classification.json")
                    selection = read_json_artifact(run_id, "selection.json")
                    
                    with host:
                        with ui.tabs().classes("w-full") as tabs:
                            t_overview = ui.tab("Overview")
                            t_timeline = ui.tab("Timeline")
                            t_stages = ui.tab("Stages")
                            t_rejected = ui.tab("Rejected Jobs")
                            t_artifacts = ui.tab("Artifacts")
                            t_env = ui.tab("Environment")
                            t_state = ui.tab("Legacy State")
                            
                        with ui.tab_panels(tabs, value=t_overview).classes("w-full h-full min-h-[500px] bg-transparent p-0"):
                            with ui.tab_panel(t_overview).classes("p-0 h-full"):
                                with panel_p("w-full flex flex-col gap-4"):
                                    if manifest:
                                        ui.html(f'''
                                        <div class="grid grid-cols-2 gap-4 text-sm">
                                            <div><strong>Run ID:</strong> {manifest.get("run_id")}</div>
                                            <div><strong>Status:</strong> {manifest.get("status")}</div>
                                            <div><strong>Generated At:</strong> {format_datetime(manifest.get("generated_at"))}</div>
                                            <div><strong>Schema Version:</strong> {manifest.get("schema_version")}</div>
                                        </div>
                                        ''')
                                    else:
                                        ui.label("No manifest.json available for this run (legacy run).")
                                        
                                    if diagnostics:
                                        ui.html('<div class="font-bold mt-4">Diagnostics</div>')
                                        ui.html(f'''
                                        <div class="grid grid-cols-2 gap-4 text-sm text-[var(--muted)]">
                                            <div><strong>Python:</strong> {diagnostics.get("python_version", "").split(" ")[0]}</div>
                                            <div><strong>Platform:</strong> {diagnostics.get("platform")}</div>
                                            <div><strong>Hostname:</strong> {diagnostics.get("hostname")}</div>
                                            <div><strong>Git Commit:</strong> {diagnostics.get("git_commit") or "N/A"}</div>
                                        </div>
                                        ''')
                            
                            with ui.tab_panel(t_timeline).classes("p-0 h-full flex flex-col"):
                                with panel_p("w-full h-full flex flex-col gap-2"):
                                    if timeline:
                                        import copy
                                        t_copy = copy.deepcopy(timeline)
                                        for t in t_copy:
                                            t['started_at'] = format_datetime(t.get('started_at'))
                                            t['completed_at'] = format_datetime(t.get('completed_at'))
                                            t['duration'] = format_duration(t.get('duration_ms'))
                                        DataTable(pd.DataFrame(t_copy), classes="w-full h-full flex-grow", table_id="timeline_table")
                                    else:
                                        ui.label("No timeline data.")
                                        
                            with ui.tab_panel(t_stages).classes("p-0 h-full flex flex-col gap-4 overflow-y-auto"):
                                if classification and "summary" in classification:
                                    with panel_p("w-full flex flex-col gap-2"):
                                        ui.label("Classification Summary").classes("font-bold")
                                        ui.code(json.dumps(classification["summary"], indent=2), language="json").classes("w-full bg-[var(--bg)] border border-[var(--border)] rounded text-[13px]")
                                if selection:
                                    with panel_p("w-full flex flex-col gap-2"):
                                        ui.label("Selection Summary").classes("font-bold")
                                        summary = {k: v for k, v in selection.items() if k != "rejected_jobs"}
                                        ui.code(json.dumps(summary, indent=2), language="json").classes("w-full bg-[var(--bg)] border border-[var(--border)] rounded text-[13px]")
                                        
                            with ui.tab_panel(t_rejected).classes("p-0 h-full flex flex-col"):
                                with panel_p("w-full h-full flex flex-col gap-2"):
                                    rejected = []
                                    if classification and "rejected_jobs" in classification:
                                        rejected.extend(classification["rejected_jobs"])
                                    if selection and "rejected_jobs" in selection:
                                        rejected.extend(selection["rejected_jobs"])
                                        
                                    application = read_json_artifact(run_id, "application.json")
                                    if application and "rejected_jobs" in application:
                                        rejected.extend(application["rejected_jobs"])
                                        
                                    if classification and "rejection_summary" in classification:
                                        ui.label("Overall Rejection Analytics").classes("font-bold mt-2")
                                        ui.code(json.dumps(classification["rejection_summary"], indent=2), language="json").classes("w-full bg-[var(--bg)] border border-[var(--border)] rounded text-[13px] mb-4")

                                    if rejected:
                                        group_by = ui.select(["None", "Stage", "Code", "Company", "Search Query"], value="None", label="Group By").classes("w-48 mb-2")
                                        table_container = ui.column().classes("w-full h-full flex-grow")
                                        
                                        def update_rejected_table():
                                            table_container.clear()
                                            df = pd.DataFrame(rejected)
                                            with table_container:
                                                if group_by.value == "None":
                                                    DataTable(df, classes="w-full h-full flex-grow", table_id="rejected_table")
                                                else:
                                                    col = group_by.value.lower().replace(" ", "_")
                                                    if col in df.columns:
                                                        grouped = df[col].value_counts().reset_index()
                                                        grouped.columns = [group_by.value, 'Count']
                                                        DataTable(grouped, classes="w-full h-full flex-grow", table_id="rejected_table_grouped")
                                                    else:
                                                        ui.label(f"Column '{col}' not found in data.")
                                        
                                        group_by.on_value_change(lambda _: update_rejected_table())
                                        update_rejected_table()
                                    else:
                                        ui.label("No rejected jobs tracked in this run.")
                                        
                            with ui.tab_panel(t_artifacts).classes("p-0 h-full flex flex-col"):
                                with panel_p("w-full h-full flex flex-col gap-2"):
                                    files = payload.get("files", [])
                                    if files:
                                        DataTable(pd.DataFrame(files), classes="w-full h-full min-h-[400px] flex-grow", table_id="artifacts_table")
                                    else:
                                        ui.label("No artifacts generated.")
                                        
                            with ui.tab_panel(t_env).classes("p-0 h-full flex flex-col"):
                                with panel_p("w-full h-full flex flex-col gap-2"):
                                    if environment:
                                        ui.code(json.dumps(environment, indent=2), language="json").classes("w-full h-full bg-[var(--bg)] border border-[var(--border)] rounded overflow-y-auto text-[13px]")
                                    else:
                                        ui.label("No environment config tracked.")
                                        
                            with ui.tab_panel(t_state).classes("p-0 h-full flex flex-col"):
                                with panel_p("w-full h-full flex flex-col"):
                                    ui.code(json.dumps(payload.get("state", {}), indent=2), language="json").classes("w-full h-full bg-[var(--bg)] border border-[var(--border)] rounded overflow-y-auto text-[13px]")
                                    
                select.on_value_change(lambda _: render())
                render()
