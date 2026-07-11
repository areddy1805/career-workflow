from nicegui import ui
from datetime import datetime, UTC

from career_ui.shell import shell
from career_ui.layouts.page import page_header, section_header, metrics_grid, split_pane
from career_ui.components.cards import metric_card, panel, panel_p
from career_ui.components.badges import status_badge
from career_ui.components.feedback import callout
from career_ui.tables.data_table import DataTable
from career_ui.widgets.stage_rail import stage_rail
from career_ui.widgets.funnel import funnel

from career_ui.services.control_center import (
    application_summary,
    latest_run,
    pipeline_is_running,
    refresh_process_state,
    run_count,
    run_history,
    read_manual_action_queue,
    read_manual_jobs,
    get_workflow_queue,
    read_applications,
    review_cases,
)

def _run_projection(frame):
    if frame is None or frame.empty:
        return frame
    cols = [c for c in ("run_id", "status", "dry_run", "acquired", "selected", "submitted", "failed", "started_at") if c in frame.columns]
    return frame[cols].copy()

@ui.page("/")
def page():
    shell("/")
    
    with ui.column().classes("w-full max-w-7xl mx-auto p-6 gap-6"):
        state = refresh_process_state()
        run = latest_run()
        apps = application_summary()
        
        process = str(state.get("status", "IDLE")).upper()
        artifact = str(run.get("status", "UNKNOWN")).upper()
        running = pipeline_is_running()
        
        page_header(
            title="Command Center",
            subtitle="Operational cockpit for the Career Workflow engine.",
            kicker="Dashboard",
            status=process
        )
        
        # Row 1: System Health / Pipeline State
        with metrics_grid(cols=4):
            metric_card("Scheduler State", process, "Live orchestration process")
            metric_card("Active Pipeline", "IDLE" if not running else "RUNNING", "Current execution")
            metric_card("Latest Artifact", artifact, "Last completed state")
            metric_card("Heartbeat", "ONLINE", "System health check")
            
        if artifact == "ORPHANED" and not running:
            callout(
                title="Artifact requires attention",
                body="The latest run artifact is ORPHANED, but no live process owns it. Treat the artifact as historical state; use Run Inspector for evidence or Pipeline Control for a new execution.",
                type="warning"
            )
            
        # Compute actual Manual Queue count
        try:
            mq_frame = read_manual_action_queue()
            mq_auto_pending = int((mq_frame.status == "PENDING").sum()) if not mq_frame.empty and "status" in mq_frame else 0
        except Exception:
            mq_auto_pending = 0
            
        try:
            mj_frame = read_manual_jobs()
            mj_pending = int((mj_frame.status.isin(["TO_APPLY", "SHORTLISTED"])).sum()) if not mj_frame.empty and "status" in mj_frame else 0
        except Exception:
            mj_pending = 0
            
        manual_queue_count = mq_auto_pending + mj_pending

        # Compute actual Workflow Queue count
        try:
            wq = get_workflow_queue()
            wq_items = wq.list()
            workflow_queue_count = len(wq_items) if wq_items else 0
        except Exception:
            workflow_queue_count = 0

        # Row 2: Secondary Metrics
        with metrics_grid(cols=4):
            metric_card("Applications Today", f"{run_count(run,'submitted'):,}", "Latest run submissions")
            metric_card("Manual Queue", f"{manual_queue_count:,}", "Items requiring review")
            metric_card("Workflow Queue", f"{workflow_queue_count:,}", "Qualified opportunities")
            metric_card("Total Portfolio", f"{int(apps.get('total',0)):,}", "Lifetime tracked")

        # Row 3: Pipeline / Activity
        with ui.row().classes("w-full gap-6 flex-nowrap"):
            # Left side: execution map
            with ui.column().classes("w-2/3 gap-2"):
                section_header("Active Pipeline Timeline", "Latest artifact-backed stage progression")
                stages = run.get("stages") or {
                    "preflight": "PENDING",
                    "acquisition": "PENDING",
                    "classification": "PENDING",
                    "selection": "PENDING",
                    "application": "PENDING",
                    "reconciliation": "PENDING",
                    "report": run.get("status", "UNKNOWN"),
                }
                stage_rail(stages)
                
                ui.html('<div class="mt-4"></div>')
                section_header("Recent Completions", "Compact execution history")
                DataTable(_run_projection(run_history(8)))

            # Right side: Funnel & Alerts
            with ui.column().classes("w-1/3 gap-2"):
                section_header("Application Funnel", "Portfolio lifecycle distribution")
                funnel([
                    ("Submitted", apps.get("submitted", apps.get("total", 0))),
                    ("Viewed", apps.get("viewed", 0)),
                    ("Shortlisted", apps.get("shortlisted", 0)),
                    ("Interview", apps.get("interview", 0)),
                    ("Offer", apps.get("offer", 0)),
                ])
                
                ui.html('<div class="mt-4"></div>')
                section_header("Action Required", "Recommendations")
                
                # Compute actual review cases count
                try:
                    rc_frame = review_cases()
                    review_count = len(rc_frame) if rc_frame is not None and not rc_frame.empty else 0
                except Exception:
                    review_count = 0
                    
                # Compute actual stale jobs count
                try:
                    apps_df = read_applications()
                    if not apps_df.empty and "last_updated_at" in apps_df.columns:
                        now = datetime.now(UTC)
                        stale_count = 0
                        for dt_str in apps_df["last_updated_at"].dropna():
                            try:
                                dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
                                if (now - dt).days >= 7:
                                    stale_count += 1
                            except Exception:
                                pass
                    else:
                        stale_count = 0
                except Exception:
                    stale_count = 0

                with panel_p("flex flex-col gap-3 w-full"):
                    if review_count > 0:
                        callout("Review Queue", f"You have {review_count} item{'s' if review_count != 1 else ''} pending manual review.", type="info", classes="border-l-[3px]")
                    elif manual_queue_count > 0:
                        callout("Manual Queue", f"You have {manual_queue_count} item{'s' if manual_queue_count != 1 else ''} pending in the manual queue.", type="info", classes="border-l-[3px]")
                    else:
                        callout("All Clear", "No items pending manual review.", type="positive", classes="border-l-[3px]")
                        
                    if stale_count > 0:
                        callout("Stale Jobs", f"{stale_count} job{'s' if stale_count != 1 else ''} have not been updated in 7 days.", type="warning", classes="border-l-[3px]")

