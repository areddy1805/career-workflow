from __future__ import annotations

import streamlit as st

from control_center.data import (
    application_summary,
    calculate_duration,
    latest_run,
    lifecycle_distribution,
    read_manual_action_queue,
    review_cases,
    run_history,
)
from control_center.diagnostics import collect_health_checks, required_health_ok
from control_center.manual_jobs import read_manual_jobs
from control_center.runner import refresh_process_state


def _last_run_with_status(history, status: str) -> str:
    if history.empty or "status" not in history.columns:
        return "—"
    matches = history.loc[
        history["status"].fillna("").astype(str).str.upper().eq(status)
    ]
    if matches.empty:
        return "—"
    row = matches.iloc[0]
    return str(row.get("completed_at") or row.get("run_id") or "—")


def render() -> None:
    st.title("Dashboard")
    st.caption("Current pipeline, application, queue, and recruiting lifecycle state.")

    actions = st.columns([1, 1, 5])
    if actions[0].button("Go to Pipeline", type="primary"):
        st.session_state["navigation_target"] = "Pipeline"
        st.rerun()
    if actions[1].button("Refresh Data"):
        st.rerun()

    checks = collect_health_checks()
    process = refresh_process_state()
    run = latest_run()
    history = run_history(limit=50)
    summary = application_summary()
    review = review_cases()
    external = read_manual_action_queue()
    manual_jobs = read_manual_jobs()

    if required_health_ok(checks):
        st.success("System preflight: READY")
    else:
        st.error("System preflight: BLOCKED — inspect System Health")

    st.subheader("Pipeline Health")
    health = st.columns(6)
    health[0].metric("Process State", process.get("status", "IDLE"))
    health[1].metric("Latest Run", run.get("status", "NO RUN"))
    health[2].metric(
        "Mode",
        "DRY RUN" if run.get("dry_run") is True
        else "LIVE" if run.get("dry_run") is False
        else "UNKNOWN",
    )
    health[3].metric(
        "Duration",
        calculate_duration(run.get("started_at"), run.get("completed_at")),
    )
    health[4].metric("Last Success", _last_run_with_status(history, "SUCCESS"))
    health[5].metric("Last Failure", _last_run_with_status(history, "FAILED"))

    st.subheader("Latest Run")
    st.caption(
        f"Run ID: {run.get('run_id', '—')} | "
        f"Started: {run.get('started_at', '—')} | "
        f"Completed: {run.get('completed_at', '—')}"
    )
    run_metrics = st.columns(8)
    values = (
        ("Acquired", run.get("acquired", 0)),
        ("Classified", run.get("classified", 0)),
        ("Selected", run.get("selected", 0)),
        ("Attempted", run.get("attempted", 0)),
        ("Submitted", run.get("submitted", 0)),
        ("Already Applied", run.get("already_applied", 0)),
        ("Failed", run.get("failed", 0)),
        ("Manual Review", run.get("manual_review", 0)),
    )
    for column, (label, value) in zip(run_metrics, values, strict=True):
        column.metric(label, value)

    st.subheader("Operational Queues")
    queue_metrics = st.columns(3)
    queue_metrics[0].metric("Review Cases", len(review))
    queue_metrics[1].metric("Pipeline External Actions", len(external))
    queue_metrics[2].metric("Tracked External Jobs", len(manual_jobs))

    st.subheader("Application Lifecycle")
    lifecycle_metrics = st.columns(7)
    lifecycle_values = (
        ("Applications", summary["total"]),
        ("Submitted", summary["submitted"]),
        ("Viewed", summary["viewed"]),
        ("Shortlisted", summary["shortlisted"]),
        ("Interview", summary["interview"]),
        ("Rejected", summary["rejected"]),
        ("Offer", summary["offer"]),
    )
    for column, (label, value) in zip(
        lifecycle_metrics, lifecycle_values, strict=True
    ):
        column.metric(label, value)

    distribution = lifecycle_distribution()
    if not distribution.empty:
        st.bar_chart(distribution.set_index("lifecycle_stage"))

    st.subheader("Recent Runs")
    if history.empty:
        st.info("No pipeline run history found.")
    else:
        st.dataframe(history.head(10), use_container_width=True, hide_index=True)
