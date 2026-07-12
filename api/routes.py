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
    read_run_result
)
from control_center.runtime_status import (
    get_scheduler_runtime,
    get_pipeline_runtime,
    get_ui_runtime,
    get_latest_run_runtime
)

router = APIRouter()

def df_to_dict(df: pd.DataFrame) -> list[dict[str, Any]]:
    return df.fillna("").to_dict(orient="records")

@router.get("/dashboard")
def get_dashboard() -> dict[str, Any]:
    summary = application_summary()
    lifecycle = df_to_dict(lifecycle_distribution())
    latest = latest_run()
    
    return {
        "summary": summary,
        "lifecycle": lifecycle,
        "latest_run": latest
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
