import html
from nicegui import ui

from career_ui.shell import shell
from career_ui.layouts.page import page_header, section_header, metrics_grid, split_pane
from career_ui.components.cards import panel_p, metric_card
from career_ui.tables.data_table import DataTable
from career_ui.utils.formatting import format_datetime
from career_ui.widgets.stage_rail import stage_rail

from career_ui.services.control_center import (
    calculate_duration,
    latest_run,
    latest_terminal_run,
    launch_pipeline,
    pipeline_is_running,
    read_pipeline_log,
    refresh_process_state,
    run_history,
)

def _run_projection(frame):
    if frame is None or frame.empty:
        return frame
    cols = [c for c in ("run_id", "status", "dry_run", "acquired", "selected", "submitted", "failed", "started_at") if c in frame.columns]
    return frame[cols]

def _calculate_eta(current_run) -> str:
    from control_center.run_inspector import read_json_artifact
    from control_center.data import list_run_directories

    stages = current_run.get("stages", {})
    running_stage = next((s for s, status in stages.items() if status == "RUNNING"), None)
    if not running_stage:
        return "—"

    durations = []
    for run_dir in list_run_directories()[:10]:
        timeline = read_json_artifact(run_dir.name, "timeline.json")
        if timeline and isinstance(timeline, list):
            for t in timeline:
                if t.get("stage") == running_stage and t.get("status") == "SUCCESS":
                    durations.append(t.get("duration_ms", 0))

    if not durations:
        return "Calculating..."

    avg_ms = sum(durations) / len(durations)

    # We should subtract the time already spent in the current stage
    # But for simplicity and to avoid fake precision, just return the average duration
    # or remaining duration.
    # The requirement says:
    # "remaining = average(stage historical durations)"
    # "Never show fake precision"

    avg_seconds = avg_ms / 1000
    if avg_seconds < 60:
        return "< 1 min"
    return f"~{int(avg_seconds // 60)} min"

@ui.page("/pipeline")
def page():
    shell("/pipeline")

    with ui.column().classes("w-full max-w-[1600px] mx-auto p-4 gap-6 pb-20"):
        state = refresh_process_state()
        process = str(state.get("status", "IDLE")).upper()

        page_header(
            "Pipeline Control",
            "Configure, execute, and observe the application engine.",
            kicker="Operate",
            status=process,
        )

        with split_pane():

            # Left Column (Logs and History)
            with ui.column().classes("flex-[1.8] min-w-0 gap-6"):

                with panel_p("w-full flex flex-col"):
                    section_header("Live Output", "Active launcher log")
                    log_box = ui.html("").classes("w-full h-[500px] bg-[#0b1017] border border-[#1d2938] rounded p-4 overflow-y-auto font-mono text-[13px] text-[#9dacbf] leading-relaxed")

                section_header("Run History", "Recent execution artifacts")
                history_box = ui.column().classes("w-full h-80 min-w-0")
                with history_box:
                    DataTable(_run_projection(run_history(20)), classes="h-full")

            # Right Column (Config and Telemetry)
            with ui.column().classes("flex-[1] min-w-[320px] gap-6"):

                with panel_p("w-full flex flex-col gap-4"):
                    section_header("Run Configuration", "Safety-first execution controls")
                    mode = ui.toggle(["Dry Run", "Live"], value="Dry Run").props("spread").classes("w-full")
                    limit = ui.number("Application ceiling", value=500, min=1, max=1000).classes("w-full text-sm")
                    canary = ui.switch("Canary · one live application").classes("text-sm")
                    force_live = ui.switch("Force Live · Bypass challenge cooldown").classes("text-sm")
                    confirm = ui.checkbox("I understand LIVE mode can submit applications").classes("text-sm text-[var(--danger)]")

                    def mode_change():
                        live = mode.value == "Live"
                        canary.set_visibility(live)
                        confirm.set_visibility(live)
                        limit.value = 3 if live else 500

                    mode.on_value_change(lambda _: mode_change())
                    mode_change()

                    async def launch():
                        live = mode.value == "Live"
                        if live and not confirm.value:
                            ui.notify("Live confirmation is required", type="warning")
                            return
                        try:
                            launch_pipeline(
                                live=live,
                                max_applications=int(limit.value),
                                canary=bool(canary.value),
                                force_live=bool(force_live.value),
                            )
                            ui.notify("Pipeline launched", type="positive")
                            render_state()
                        except Exception as e:
                            ui.notify(str(e), type="negative")

                    ui.button("Launch Pipeline", icon="rocket_launch", on_click=launch).props("color=primary unelevated").classes("w-full font-bold shadow-lg")

                metrics = ui.column().classes("w-full gap-4")

                with panel_p("w-full flex flex-col gap-2"):
                    section_header("Execution Map", "Latest terminal artifact")
                    latest = latest_terminal_run()
                    stage_box = ui.column().classes("w-full")

        def render_state():
            metrics.clear()
            stage_box.clear()

            state = refresh_process_state()
            running = pipeline_is_running()

            with metrics:
                section_header("Live Process Telemetry")
                with metrics_grid(cols=2):
                    metric_card("Process", state.get("status", "IDLE"))
                    metric_card("PID", state.get("pid") or "—")
                    metric_card("Mode", "LIVE" if state.get("live") else "DRY RUN")
                    metric_card("Elapsed", calculate_duration(state.get("started_at"), state.get("completed_at")))
                    if running:
                        metric_card("Stage ETA", _calculate_eta(latest_run()))

            current_run = latest_run()
            with stage_box:
                stage_rail(current_run.get("stages") or {
                    "preflight": "PENDING",
                    "acquisition": "PENDING",
                    "classification": "PENDING",
                    "selection": "PENDING",
                    "application": "PENDING",
                    "reconciliation": "PENDING",
                    "report": current_run.get("status", "UNKNOWN"),
                })

            content = read_pipeline_log() if running else "No active process. Historical output is available in Run Inspector."
            log_box.content = f'<pre style="margin:0;white-space:pre-wrap">{html.escape(content)}</pre>'

        render_state()
        ui.timer(2.0, render_state)
