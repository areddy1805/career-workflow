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
    top_companies,
    get_job_cache_dict
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
    cache_dict = get_job_cache_dict()
    enriched_job = df_to_dict(job_df)[0]
    
    if job_id in cache_dict:
        for k, v in cache_dict[job_id].items():
            if k not in enriched_job or not enriched_job[k]:
                enriched_job[k] = v
                
    return {
        "overview": enriched_job,
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

# --- Queues Overhaul ---

def _enrich_queue_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cache = get_job_cache_dict()
    for item in items:
        jid = item.get("job_id")
        if jid in cache:
            for k, v in cache[jid].items():
                if k not in item or not item[k]:
                    item[k] = v
    return items

@router.get("/queues/manual-review")
def api_get_manual_review_queue() -> dict[str, Any]:
    wq = get_workflow_queue()
    items = wq.list(sort_by="updated_at", sort_dir="desc")
    filtered = [i for i in items if i.get("source") == "manual_review" and i.get("workflow_status") in ("PENDING", "IN_PROGRESS", "READY")]
    return {"items": _enrich_queue_items(filtered)}

@router.get("/queues/external-apply")
def api_get_external_apply_queue() -> dict[str, Any]:
    wq = get_workflow_queue()
    items = wq.list(sort_by="updated_at", sort_dir="desc")
    filtered = [i for i in items if i.get("source") == "external_apply" and i.get("workflow_status") in ("PENDING", "IN_PROGRESS", "READY", "APPLYING")]
    return {"items": _enrich_queue_items(filtered)}

@router.get("/queues/other-action")
def api_get_other_action_queue() -> dict[str, Any]:
    wq = get_workflow_queue()
    items = wq.list(sort_by="updated_at", sort_dir="desc")
    filtered = [i for i in items if i.get("source") not in ("manual_review", "external_apply") and i.get("workflow_status") in ("PENDING", "IN_PROGRESS", "READY")]
    
    # Also include manually sourced jobs if needed, or they can just be fetched elsewhere.
    return {"items": _enrich_queue_items(filtered)}

@router.post("/queues/{job_id}/transition")
def api_queue_transition(job_id: str, req: WorkflowTransitionRequest) -> dict[str, str]:
    success = workflow_queue_transition(job_id, req.to_status, note=req.note or "")
    if not success:
        raise HTTPException(status_code=400, detail="Failed to transition job")
    return {"status": "Transitioned"}

@router.post("/queues/manual")
def api_add_manual_job(req: ManualJobRequest) -> dict[str, str]:
    try:
        from control_center.manual_jobs import add_manual_job
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

# --- Search Intelligence ---

@router.get("/search-intelligence")
def api_get_search_intelligence() -> dict[str, Any]:
    from src.search.planner import SearchPlanner
    planner = SearchPlanner()
    queries = planner.generate_queries()

    # Technology profile breakdown for Search Intelligence UI
    tech_profiles: dict[str, list[str]] = {}
    for q in queries:
        tech_group = q.get("technology_group", q.get("matched_technology", "")) or "general"
        if tech_group not in tech_profiles:
            tech_profiles[tech_group] = []
        if q.get("keyword") not in tech_profiles[tech_group]:
            tech_profiles[tech_group].append(q.get("keyword", ""))

    # Provider-level query distribution (which providers each plan targets)
    provider_query_counts: dict[str, int] = {}
    try:
        plans = planner.generate_plans()
        for plan in plans:
            targets = plan.target_providers or ["all"]
            for t in targets:
                provider_query_counts[t] = provider_query_counts.get(t, 0) + 1
    except Exception:
        pass

    return {
        "active_profiles": planner.user_profile.get("active_profiles", []),
        "locations": planner.user_profile.get("preferred_locations", []),
        "country": planner.user_profile.get("country", ""),
        "remote_policy": planner.user_profile.get("remote_policy", ""),
        "total_queries": len(queries),
        "queries": queries,
        "technology_profiles": tech_profiles,
        "provider_query_counts": provider_query_counts,
    }


# --- Provider Platform ---

@router.get("/providers")
def api_list_providers() -> dict[str, Any]:
    """List all configured providers with their status, capabilities, and health."""
    try:
        from src.acquisition.registry import ProviderRegistry
        registry = ProviderRegistry()
        providers = registry.provider_info()
        return {"providers": providers, "total": len(providers)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/{name}")
def api_get_provider(name: str) -> dict[str, Any]:
    """Get details for a single provider."""
    try:
        from src.acquisition.registry import ProviderRegistry
        registry = ProviderRegistry()
        infos = registry.provider_info()
        for info in infos:
            if info.get("name") == name:
                return info
        raise HTTPException(status_code=404, detail=f"Provider '{name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/acquisition/summary")
def api_get_acquisition_summary() -> dict[str, Any]:
    """Return the latest provider_summary.json from the most recent run."""
    import json
    from pathlib import Path
    summary_path = _find_latest_artifact("provider_summary.json")
    if summary_path is None:
        return {"data": None, "message": "No acquisition summary found. Run the pipeline first."}
    try:
        with open(summary_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/provider-groups")
def api_get_provider_groups() -> dict[str, Any]:
    """Return provider group definitions from config/provider_groups.yaml."""
    import yaml
    from pathlib import Path
    groups_path = Path("config/provider_groups.yaml")
    if not groups_path.exists():
        return {"groups": {}}
    try:
        with open(groups_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return {"groups": data.get("groups", {})}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _find_latest_artifact(filename: str):
    """Find the most recent artifact file by scanning run directories."""
    from pathlib import Path
    runs_dir = Path("data/runs")
    if not runs_dir.exists():
        # Also check flat data directory
        flat = Path("data") / filename
        return flat if flat.exists() else None
    candidates = sorted(
        runs_dir.glob(f"*/{filename}"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None
