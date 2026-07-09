from __future__ import annotations

import streamlit as st

from control_center.data import (
    application_summary,
    calculate_duration,
    latest_run,
    lifecycle_distribution,
)
from control_center.runner import refresh_process_state


def _metric(
    label: str,
    value,
) -> None:
    st.metric(
        label,
        value if value is not None else 0,
    )


def render() -> None:
    st.title("Dashboard")

    st.caption("Current pipeline, application, and recruiting lifecycle state.")

    if st.button(
        "Refresh Data",
        type="primary",
    ):
        st.rerun()

    process = refresh_process_state()
    run = latest_run()
    applications = application_summary()

    st.subheader("Pipeline Health")

    health_columns = st.columns(4)

    health_columns[0].metric(
        "Process State",
        process.get(
            "status",
            "IDLE",
        ),
    )

    health_columns[1].metric(
        "Latest Run",
        run.get(
            "status",
            "NO RUN",
        ),
    )

    health_columns[2].metric(
        "Mode",
        (
            "DRY RUN"
            if run.get("dry_run") is True
            else "LIVE" if run.get("dry_run") is False else "UNKNOWN"
        ),
    )

    health_columns[3].metric(
        "Duration",
        calculate_duration(
            run.get("started_at"),
            run.get("completed_at"),
        ),
    )

    st.subheader("Latest Run")

    run_columns = st.columns(6)

    _values = (
        ("Acquired", run.get("acquired", 0)),
        ("Classified", run.get("classified", 0)),
        ("Selected", run.get("selected", 0)),
        ("Submitted", run.get("submitted", 0)),
        (
            "Already Applied",
            run.get(
                "already_applied",
                0,
            ),
        ),
        ("Failed", run.get("failed", 0)),
    )

    for column, (
        label,
        value,
    ) in zip(
        run_columns,
        _values,
        strict=True,
    ):
        column.metric(
            label,
            value,
        )

    st.subheader("Application Lifecycle")

    lifecycle_columns = st.columns(7)

    lifecycle_values = (
        ("Applications", applications["total"]),
        ("Submitted", applications["submitted"]),
        ("Viewed", applications["viewed"]),
        ("Shortlisted", applications["shortlisted"]),
        ("Interview", applications["interview"]),
        ("Rejected", applications["rejected"]),
        ("Offer", applications["offer"]),
    )

    for column, (
        label,
        value,
    ) in zip(
        lifecycle_columns,
        lifecycle_values,
        strict=True,
    ):
        column.metric(
            label,
            value,
        )

    distribution = lifecycle_distribution()

    if distribution.empty:
        st.info("No applications found in the ledger.")
    else:
        st.bar_chart(distribution.set_index("lifecycle_stage"))

    if run:
        st.subheader("Run Identity")

        st.code(
            run.get(
                "run_id",
                "Unknown",
            ),
            language=None,
        )
    else:
        st.info("No pipeline runs found.")
