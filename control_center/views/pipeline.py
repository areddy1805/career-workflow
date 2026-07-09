from __future__ import annotations

import streamlit as st

from control_center.data import (
    calculate_duration,
    latest_terminal_run,
    run_history,
)
from control_center.runner import (
    launch_pipeline,
    pipeline_is_running,
    read_pipeline_log,
    refresh_process_state,
)


def render() -> None:
    st.title("Pipeline")
    st.caption("Execute and inspect the existing staged Career Workflow pipeline.")

    state = refresh_process_state()
    running = pipeline_is_running()

    status_columns = st.columns(5)
    status_columns[0].metric("Process State", state.get("status", "IDLE"))
    status_columns[1].metric("PID", state.get("pid", "—"))
    status_columns[2].metric("Mode", "LIVE" if state.get("live") else "DRY RUN")
    status_columns[3].metric(
        "Elapsed",
        calculate_duration(state.get("started_at"), state.get("completed_at")),
    )
    status_columns[4].metric(
        "Exit Code",
        state.get("exit_code") if state.get("exit_code") is not None else "—",
    )

    if state.get("status") == "ORPHANED":
        st.warning(state.get("diagnostic", "Previous process state was orphaned."))

    st.divider()

    mode = st.radio(
        "Execution Mode", ["Dry Run", "Live"], horizontal=True, disabled=running
    )
    live = mode == "Live"
    max_applications = st.number_input(
        "Maximum Applications",
        min_value=1,
        max_value=1000,
        value=3 if live else 500,
        step=1,
        disabled=running,
    )

    canary = False
    if live:
        canary = st.checkbox(
            "Canary mode: force at most one application", disabled=running
        )
        st.error("LIVE MODE: this run may submit real job applications.")
        confirmed = st.checkbox(
            "I understand this run may submit real applications.", disabled=running
        )
    else:
        confirmed = True
        st.info("Dry run is active. Application submission is disabled.")

    actions = st.columns([1, 1, 4])
    if actions[0].button(
        "Run Live Pipeline" if live else "Run Dry Pipeline",
        type="primary",
        disabled=running or not confirmed,
    ):
        try:
            launch_pipeline(
                live=live, max_applications=int(max_applications), canary=canary
            )
            st.rerun()
        except Exception as error:
            st.error(f"Pipeline launch failed: {error}")

    if actions[1].button("Refresh Status"):
        refresh_process_state()
        st.rerun()

    st.divider()

    if running:
        st.subheader("Current Process Output")

        log = read_pipeline_log()

        if log:
            st.code(log, language="text")
        else:
            st.info("The active pipeline has not produced output yet.")
    else:
        st.caption(
            "No pipeline process is currently active. "
            "Historical output is available through Run Inspector."
        )

    latest = latest_terminal_run()

    st.subheader("Latest Completed Run")
    if not latest:
        st.info("No completed pipeline run found.")
    else:
        cols = st.columns(6)
        counts = latest.get("counts", {})
        cols[0].metric("Status", latest.get("status", "UNKNOWN"))
        cols[1].metric("Acquired", latest.get("acquired", counts.get("acquired", 0)))
        cols[2].metric(
            "Classified", latest.get("classified", counts.get("classified", 0))
        )
        cols[3].metric("Selected", latest.get("selected", counts.get("selected", 0)))
        cols[4].metric("Submitted", latest.get("submitted", 0))
        cols[5].metric("Failed", latest.get("failed", 0))

        stages = latest.get("stages", {})
        if stages:
            st.subheader("Stages")
            st.dataframe(
                [{"Stage": k, "Status": v} for k, v in stages.items()],
                width="stretch",
                hide_index=True,
            )

    st.subheader("Run History")
    history = run_history(limit=20)
    (
        st.dataframe(history, width="stretch", hide_index=True)
        if not history.empty
        else st.info("No run history found.")
    )
