from __future__ import annotations

import streamlit as st

from control_center.data import (
    calculate_duration,
    latest_run,
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

    status_columns = st.columns(4)

    status_columns[0].metric(
        "Process State",
        state.get(
            "status",
            "IDLE",
        ),
    )

    status_columns[1].metric(
        "PID",
        state.get(
            "pid",
            "—",
        ),
    )

    status_columns[2].metric(
        "Mode",
        ("LIVE" if state.get("live") else "DRY RUN"),
    )

    status_columns[3].metric(
        "Elapsed",
        calculate_duration(
            state.get("started_at"),
            state.get("completed_at"),
        ),
    )

    st.divider()

    mode = st.radio(
        "Execution Mode",
        options=[
            "Dry Run",
            "Live",
        ],
        horizontal=True,
        disabled=running,
    )

    live = mode == "Live"

    default_limit = 3 if live else 500

    max_applications = st.number_input(
        "Maximum Applications",
        min_value=1,
        max_value=1000,
        value=default_limit,
        step=1,
        disabled=running,
    )

    canary = False

    if live:
        canary = st.checkbox(
            "Canary mode: force at most one application",
            value=False,
            disabled=running,
        )

        st.error("LIVE MODE: this run may submit real job applications.")

        confirmed = st.checkbox(
            "I understand this run may submit real applications.",
            value=False,
            disabled=running,
        )

    else:
        confirmed = True

        st.info("Dry run is active. Application submission is disabled.")

    launch_disabled = running or not confirmed

    action_columns = st.columns(
        [
            1,
            1,
            4,
        ]
    )

    if action_columns[0].button(
        ("Run Live Pipeline" if live else "Run Dry Pipeline"),
        type="primary",
        disabled=launch_disabled,
    ):
        try:
            launch_pipeline(
                live=live,
                max_applications=int(max_applications),
                canary=canary,
            )

            st.rerun()

        except Exception as error:
            st.error(f"Pipeline launch failed: {error}")

    if action_columns[1].button(
        "Refresh Status",
    ):
        st.rerun()

    st.divider()

    st.subheader("Latest Output")

    log = read_pipeline_log()

    if log:
        st.code(
            log,
            language="text",
        )
    else:
        st.info("No pipeline output captured yet.")

    latest = latest_run()

    st.subheader("Latest Pipeline Result")

    if not latest:
        st.info("No pipeline run artifacts found.")
        return

    result_columns = st.columns(5)

    result_columns[0].metric(
        "Status",
        latest.get(
            "status",
            "UNKNOWN",
        ),
    )

    result_columns[1].metric(
        "Acquired",
        latest.get(
            "acquired",
            0,
        ),
    )

    result_columns[2].metric(
        "Classified",
        latest.get(
            "classified",
            0,
        ),
    )

    result_columns[3].metric(
        "Selected",
        latest.get(
            "selected",
            0,
        ),
    )

    result_columns[4].metric(
        "Submitted",
        latest.get(
            "submitted",
            0,
        ),
    )

    stages = latest.get(
        "stages",
        {},
    )

    if stages:
        st.subheader("Stages")

        stage_rows = [
            {
                "Stage": name,
                "Status": status,
            }
            for name, status in stages.items()
        ]

        st.dataframe(
            stage_rows,
            use_container_width=True,
            hide_index=True,
        )
