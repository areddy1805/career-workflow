from nicegui import ui
from datetime import datetime, UTC

from career_ui_legacy.shell import shell
from career_ui_legacy.layouts.page import page_header, section_header, metrics_grid, split_pane
from career_ui_legacy.components.cards import metric_card, panel, panel_p
from career_ui_legacy.components.badges import status_badge
from career_ui_legacy.components.feedback import callout
from career_ui_legacy.tables.data_table import DataTable
from career_ui_legacy.utils.formatting import format_datetime
from career_ui_legacy.widgets.stage_rail import stage_rail
from career_ui_legacy.widgets.funnel import funnel

from career_ui_legacy.services.control_center import (
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
from control_center.runtime_status import (
    get_scheduler_runtime,
    get_pipeline_runtime,
    get_ui_runtime,
    get_latest_run_runtime,
)

def _run_projection(frame):
    import pandas as pd
    if frame is None or frame.empty:
        return frame
    cols = [c for c in ("run_id", "status", "dry_run", "acquired", "selected", "submitted", "failed", "started_at") if c in frame.columns]
    df = frame[cols].copy()
    if "started_at" in df.columns:
        df["started_at"] = df["started_at"].apply(lambda x: format_datetime(x) if pd.notna(x) else x)
    return df

@ui.page("/")
def page():
    shell("/")

    with ui.column().classes("w-full max-w-7xl mx-auto p-6 gap-6"):
        ui_rt = get_ui_runtime()
        sched_rt = get_scheduler_runtime()
        pipe_rt = get_pipeline_runtime()
        last_rt = get_latest_run_runtime()

        run = latest_run()
        apps = application_summary()

        ui_status = ui_rt["status"]
        sched_status = sched_rt["status"]
        pipe_status = pipe_rt["status"]
        last_status = last_rt["status"]

        page_header(
            title="Command Center",
            subtitle="Operational cockpit for the Career Workflow engine.",
            kicker="Dashboard",
            status=sched_status
        )

        # Row 1: System Health / Pipeline State
        with metrics_grid(cols=4):
            metric_card("UI Runtime", ui_status, f"PID {ui_rt.get('pid')}")

            sched_sub = f"pid={sched_rt.get('pid')} hb={sched_rt.get('heartbeat_age', 0):.0f}s" if sched_rt.get('heartbeat_age') is not None else "No heartbeat"
            metric_card("Scheduler Runtime", sched_status, sched_sub)

            pipe_sub = f"pid={pipe_rt.get('pid')} raw={pipe_rt['raw_state'].get('status')}" if pipe_rt.get('pid') else "IDLE"
            metric_card("Pipeline Runtime", pipe_status, pipe_sub)

            metric_card("Latest Run", last_status, last_rt.get("id") or "No history")

        if pipe_status == "ORPHANED":
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

        # Calculate new metrics
        try:
            apps_df = read_applications()
            success_rate = "N/A"
            budget_rem = "N/A"
            if not apps_df.empty and "applied_at" in apps_df.columns:
                import pandas as pd
                now_utc = datetime.now(UTC)
                recent = apps_df[pd.to_datetime(apps_df["applied_at"], errors="coerce", utc=True) >= now_utc - pd.Timedelta(days=30)]
                if not recent.empty:
                    success = recent["lifecycle_stage"].str.upper().isin(["VIEWED", "SHORTLISTED", "INTERVIEW", "OFFER"]).sum()
                    success_rate = f"{(success / len(recent)) * 100:.1f}%"

                today = apps_df[pd.to_datetime(apps_df["applied_at"], errors="coerce", utc=True) >= now_utc - pd.Timedelta(days=1)]
                submitted_today = len(today)
                budget_rem = str(max(0, run.get("max_applications", 50) - submitted_today))
        except Exception:
            success_rate = "N/A"
            budget_rem = "N/A"

        classified = run.get("classified", 0)
        selected = run.get("selected", 0)
        pipeline_acceptance = f"{(selected / classified) * 100:.1f}%" if classified else "N/A"

        # Row 2: Secondary Metrics
        with metrics_grid(cols=7):
            metric_card("Apps Today", f"{run_count(run,'submitted'):,}", "Run submissions", on_click=lambda: ui.navigate.to('/jobs'))
            metric_card("Total Apps", f"{int(apps.get('total',0)):,}", "Lifetime tracked", on_click=lambda: ui.navigate.to('/jobs'))
            metric_card("Man. Queue", f"{manual_queue_count:,}", "Requires review", on_click=lambda: ui.navigate.to('/manual-queue'))
            metric_card("WF Queue", f"{workflow_queue_count:,}", "Qualified", on_click=lambda: ui.navigate.to('/workflow-queue'))
            metric_card("Pipeline Acc.", pipeline_acceptance, "Classified -> Selected")
            metric_card("Budget Rem.", budget_rem, "Daily limit remaining")
            metric_card("30d Success", success_rate, "Viewed/Interviewed")

        # Row 3: Pipeline / Activity
        with ui.row().classes("w-full gap-6 flex-nowrap items-start"):
            # Left side: execution map
            with ui.column().classes("flex-[2] min-w-0 gap-2"):
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
            with ui.column().classes("flex-[1] min-w-[320px] gap-2"):
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
                                if dt.tzinfo is None:
                                    dt = dt.replace(tzinfo=UTC)
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
                        callout("Review Queue", f"You have {review_count} item{'s' if review_count != 1 else ''} pending manual review.", type="info", classes="border-l-[3px]", on_click=lambda: ui.navigate.to('/review-queue'))
                    elif manual_queue_count > 0:
                        callout("Manual Queue", f"You have {manual_queue_count} item{'s' if manual_queue_count != 1 else ''} pending in the manual queue.", type="info", classes="border-l-[3px]", on_click=lambda: ui.navigate.to('/manual-queue'))
                    else:
                        callout("All Clear", "No items pending manual review.", type="positive", classes="border-l-[3px]")

                    if stale_count > 0:
                        callout("Stale Jobs", f"{stale_count} job{'s' if stale_count != 1 else ''} have not been updated in 7 days.", type="warning", classes="border-l-[3px]")

