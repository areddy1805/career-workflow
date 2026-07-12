from fastapi import APIRouter, HTTPException
from typing import Any
import pandas as pd
import json

from control_center.data import (
    application_summary,
    lifecycle_distribution,
    priority_distribution,
    subtrack_distribution,
    latest_run,
    run_history,
    read_applications,
    read_application_events,
    safe_settings,
    runs_path,
    read_run_state,
    read_run_result,
    system_health,
    upcoming_executions,
    top_companies
)
from control_center.runtime_status import (
    get_scheduler_runtime,
    get_pipeline_runtime,
    get_ui_runtime,
    get_latest_run_runtime
)
from control_center.runner import (
    launch_pipeline,
    pipeline_is_running,
    read_pipeline_log,
    refresh_process_state
)
from control_center.manual_jobs import (
    add_manual_job,
    read_manual_jobs,
)
from control_center.review_state import (
    get_review_states,
    mark_reviewed,
    dismiss_job
)
from career_ui_legacy.services.control_center import (
    get_workflow_queue,
    get_queue_analytics,
    workflow_queue_transition,
    workflow_queue_add_note,
    workflow_queue_retry,
    latest_terminal_run
)
from control_center.run_inspector import read_json_artifact
from api.schemas import (
    PipelineLaunchRequest,
    ManualJobRequest,
    WorkflowTransitionRequest,
    WorkflowNoteRequest
)

router = APIRouter()

def df_to_dict(df: pd.DataFrame) -> list[dict[str, Any]]:
    return df.fillna("").to_dict(orient="records")

@router.get("/dashboard")
def get_dashboard() -> dict[str, Any]:
    summary = application_summary()
    lifecycle = df_to_dict(lifecycle_distribution())
    latest = latest_run()
    health = system_health()
    upcoming = upcoming_executions()
    companies = top_companies()
    
    return {
        "summary": summary,
        "lifecycle": lifecycle,
        "latest_run": latest,
        "system_health": health,
        "upcoming_executions": upcoming,
        "top_companies": companies
    }

@router.get("/jobs")
def get_jobs() -> list[dict[str, Any]]:
    df = read_applications()
    return df_to_dict(df)

@router.get("/jobs/{job_id}")
def get_job_details(job_id: str) -> dict[str, Any]:
    df = read_applications()
    job_df = df[df["job_id"] == job_id]
    if job_df.empty:
        raise HTTPException(status_code=404, detail="Job not found")
        
    events_df = read_application_events(job_id)
    return {
        "overview": df_to_dict(job_df)[0],
        "events": df_to_dict(events_df)
    }

@router.get("/runs")
def get_runs() -> list[dict[str, Any]]:
    df = run_history(limit=100)
    return df_to_dict(df)

@router.get("/runs/{run_id}")
def get_run_details(run_id: str) -> dict[str, Any]:
    df = run_history(limit=100)
    run_df = df[df["run_id"] == run_id]
    if run_df.empty:
        raise HTTPException(status_code=404, detail="Run not found")
        
    return df_to_dict(run_df)[0]

@router.get("/runtime")
def get_runtime() -> dict[str, Any]:
    scheduler = get_scheduler_runtime()
    pipeline = get_pipeline_runtime()
    ui = get_ui_runtime()
    latest = get_latest_run_runtime()
    return {
        "scheduler": scheduler,
        "pipeline": pipeline,
        "ui": ui,
        "latest_run": latest
    }

@router.get("/settings")
def get_settings() -> dict[str, Any]:
    return safe_settings()

@router.get("/artifacts")
def get_artifacts() -> list[dict[str, Any]]:
    path = runs_path()
    if not path.exists():
        return []
        
    directories = sorted(
        (p for p in path.iterdir() if p.is_dir()),
        key=lambda p: p.name,
        reverse=True,
    )
    
    artifacts = []
    for d in directories:
        state = read_run_state(d)
        result = read_run_result(d)
        artifacts.append({
            "run_id": d.name,
            "state": state,
            "result": result
        })
    return artifacts

# --- Pipeline Control ---

@router.get("/pipeline/state")
def api_pipeline_state() -> dict[str, Any]:
    state = refresh_process_state()
    running = pipeline_is_running()
    log = read_pipeline_log() if running else "No active process."
    return {
        "state": state,
        "running": running,
        "log": log
    }

@router.post("/pipeline/launch")
def api_pipeline_launch(req: PipelineLaunchRequest) -> dict[str, str]:
    try:
        launch_pipeline(
            live=req.live,
            max_applications=req.max_applications,
            canary=req.canary,
            force_live=req.force_live
        )
        return {"status": "Pipeline launched"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Manual Queue ---

@router.get("/queues/manual")
def api_get_manual_queue() -> dict[str, Any]:
    auto_detected = []
    run_id = latest_terminal_run()
    if run_id:
        manual = read_json_artifact(run_id, "manual_review.json") or []
        external = read_json_artifact(run_id, "external_apply.json") or []
        raw_auto = manual + external
        
        states = get_review_states()
        for job in raw_auto:
            jid = job.get("job_id")
            state = states.get(jid)
            if state:
                job["review_status"] = state.get("status")
                job["review_note"] = state.get("note")
            else:
                job["review_status"] = "PENDING"
                job["review_note"] = ""
                
        # Filter out dismissed jobs
        auto_detected = [j for j in raw_auto if j.get("review_status") != "DISMISSED"]
        
    manual_sourced = df_to_dict(read_manual_jobs())
    return {
        "auto_detected": auto_detected,
        "manual_sourced": manual_sourced
    }

@router.post("/queues/manual")
def api_add_manual_job(req: ManualJobRequest) -> dict[str, str]:
    try:
        add_manual_job(
            title=req.title,
            company=req.company,
            location=req.location,
            source=req.source,
            source_url=req.source_url,
            priority=req.priority,
            notes=req.notes or ""
        )
        return {"status": "Job added"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/queues/manual/{job_id}/transition")
def api_manual_transition(job_id: str, req: WorkflowTransitionRequest) -> dict[str, str]:
    if req.to_status.upper() == "DISMISSED":
        dismiss_job(job_id, req.note or "")
    elif req.to_status.upper() == "REVIEWED":
        mark_reviewed(job_id, req.note or "")
    else:
        raise HTTPException(status_code=400, detail="Invalid status for auto-detected queue")
    return {"status": "Transitioned"}

# --- Review Queue ---

@router.get("/queues/review")
def api_get_review_queue() -> list[dict[str, Any]]:
    run_id = latest_terminal_run()
    if not run_id:
        return []
    jobs = read_json_artifact(run_id, "selected_jobs.json") or []
    
    states = get_review_states()
    for job in jobs:
        jid = job.get("job_id")
        state = states.get(jid)
        if state:
            job["review_status"] = state.get("status")
        else:
            job["review_status"] = "PENDING"
            
    return [j for j in jobs if j.get("review_status") != "DISMISSED"]

# --- Workflow Queue ---

@router.get("/queues/workflow")
def api_get_workflow_queue() -> dict[str, Any]:
    wq = get_workflow_queue()
    analytics = get_queue_analytics(wq)
    funnel = analytics.conversion_funnel()
    items = wq.list(sort_by="updated_at", sort_dir="desc")
    
    return {
        "funnel": funnel,
        "items": items
    }

@router.post("/queues/workflow/{job_id}/transition")
def api_workflow_transition(job_id: str, req: WorkflowTransitionRequest) -> dict[str, str]:
    success = workflow_queue_transition(job_id, req.to_status, note=req.note or "")
    if not success:
        raise HTTPException(status_code=400, detail="Failed to transition job")
    return {"status": "Transitioned"}

# --- Search Intelligence ---

@router.get("/search-intelligence")
def api_get_search_intelligence() -> dict[str, Any]:
    from src.search.planner import SearchPlanner
    planner = SearchPlanner()
    queries = planner.generate_queries()
    
    return {
        "active_profiles": planner.user_profile.get("active_profiles", []),
        "locations": planner.user_profile.get("preferred_locations", []),
        "total_queries": len(queries),
        "queries": queries
    }

