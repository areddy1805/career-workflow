from __future__ import annotations

import pandas as pd
import streamlit as st

from control_center.data import (
    application_summary,
    lifecycle_distribution,
    priority_distribution,
    read_applications,
    run_history,
    subtrack_distribution,
)


def render() -> None:
    st.title("Analytics")
    st.caption("Application funnel, response metrics, portfolio mix, and run performance.")

    summary = application_summary()
    applications = read_applications()

    total = summary["total"]
    responded = sum(
        summary[key]
        for key in ("viewed", "shortlisted", "interview", "rejected", "offer")
    )
    response_rate = (responded / total * 100.0) if total else 0.0
    interview_rate = (
        (summary["interview"] + summary["offer"]) / total * 100.0
        if total else 0.0
    )
    offer_rate = (summary["offer"] / total * 100.0) if total else 0.0

    metrics = st.columns(4)
    metrics[0].metric("Total Applications", total)
    metrics[1].metric("Response Rate", f"{response_rate:.1f}%")
    metrics[2].metric("Interview Rate", f"{interview_rate:.1f}%")
    metrics[3].metric("Offer Rate", f"{offer_rate:.1f}%")

    left, right = st.columns(2)

    with left:
        st.subheader("Lifecycle Distribution")
        lifecycle = lifecycle_distribution()
        if lifecycle.empty:
            st.info("Insufficient lifecycle data.")
        else:
            st.bar_chart(lifecycle.set_index("lifecycle_stage"))

    with right:
        st.subheader("Priority Distribution")
        priority = priority_distribution()
        if priority.empty:
            st.info("Insufficient priority data.")
        else:
            st.bar_chart(priority.set_index("priority"))

    st.subheader("Subtrack Distribution")
    subtrack = subtrack_distribution()
    if subtrack.empty:
        st.info("Insufficient subtrack data.")
    else:
        st.bar_chart(subtrack.set_index("subtrack"))

    st.subheader("Application Velocity")
    if applications.empty or "applied_at" not in applications.columns:
        st.info("Insufficient application timestamp data.")
    else:
        timestamps = pd.to_datetime(
            applications["applied_at"], errors="coerce", utc=True
        )
        velocity = (
            timestamps.dropna()
            .dt.date.value_counts()
            .sort_index()
            .rename_axis("date")
            .reset_index(name="applications")
        )
        if velocity.empty:
            st.info("Insufficient application timestamp data.")
        else:
            st.line_chart(velocity.set_index("date"))

    st.subheader("Pipeline Run History")
    history = run_history(limit=30)
    if history.empty:
        st.info("No run history found.")
    else:
        st.dataframe(history, use_container_width=True, hide_index=True)

        numeric_columns = [
            c for c in ("acquired", "classified", "selected", "submitted", "failed")
            if c in history.columns
        ]
        if numeric_columns:
            chart = history[["run_id", *numeric_columns]].copy()
            chart = chart.set_index("run_id")
            st.bar_chart(chart)
