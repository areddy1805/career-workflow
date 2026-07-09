from __future__ import annotations

import pandas as pd
import streamlit as st

from control_center.analytics_helpers import (
    application_age_distribution,
    average_time_to_first_response_hours,
    score_band_distribution,
    segment_funnel,
)
from control_center.data import (
    application_summary,
    lifecycle_distribution,
    read_applications,
    run_history,
)
from control_center.workflows import run_application_report


def render() -> None:
    st.title("Analytics")
    st.caption(
        "Application funnel, response metrics, portfolio mix, age, velocity, and run performance."
    )

    applications = read_applications()
    summary = application_summary()

    total = summary["total"]
    responded = sum(
        summary[key]
        for key in ("viewed", "shortlisted", "interview", "rejected", "offer")
    )
    response_rate = responded / total * 100.0 if total else 0.0
    interview_rate = (
        (summary["interview"] + summary["offer"]) / total * 100.0
        if total else 0.0
    )
    offer_rate = summary["offer"] / total * 100.0 if total else 0.0
    average_response = average_time_to_first_response_hours(applications)

    metrics = st.columns(5)
    metrics[0].metric("Total Applications", total)
    metrics[1].metric("Response Rate", f"{response_rate:.1f}%")
    metrics[2].metric("Interview Rate", f"{interview_rate:.1f}%")
    metrics[3].metric("Offer Rate", f"{offer_rate:.1f}%")
    metrics[4].metric(
        "Avg First Response",
        f"{average_response:.1f}h" if average_response is not None else "—",
    )

    with st.expander("Run Existing Application Report"):
        if st.button("Generate Report"):
            with st.spinner("Running application_report.py..."):
                result = run_application_report()
            if result.ok:
                st.success("Application report completed.")
            else:
                st.error(f"Report failed with exit code {result.returncode}.")
            st.code(result.stdout or "No output.", language="text")

    lifecycle = lifecycle_distribution()
    if not lifecycle.empty:
        st.subheader("Lifecycle Distribution")
        st.bar_chart(lifecycle.set_index("lifecycle_stage"))

    if not applications.empty and "applied_at" in applications.columns:
        st.subheader("Application Velocity")
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
        if not velocity.empty:
            st.line_chart(velocity.set_index("date"))

    age = application_age_distribution(applications)
    score_bands = score_band_distribution(applications)

    left, right = st.columns(2)
    with left:
        st.subheader("Application Age")
        if age.empty:
            st.info("Insufficient application age data.")
        else:
            st.bar_chart(age.set_index("age_band"))
    with right:
        st.subheader("Score Bands")
        if score_bands.empty:
            st.info("Insufficient score data.")
        else:
            st.bar_chart(score_bands.set_index("score_band"))

    st.subheader("Performance by Priority")
    priority = segment_funnel(applications, "priority")
    if priority.empty:
        st.info("Insufficient priority data.")
    else:
        st.dataframe(priority, use_container_width=True, hide_index=True)

    st.subheader("Performance by Subtrack")
    subtrack = segment_funnel(applications, "subtrack")
    if subtrack.empty:
        st.info("Insufficient subtrack data.")
    else:
        st.dataframe(subtrack, use_container_width=True, hide_index=True)

    st.subheader("Pipeline Run History")
    history = run_history(limit=30)
    if history.empty:
        st.info("No run history found.")
    else:
        st.dataframe(history, use_container_width=True, hide_index=True)
        numeric_columns = [
            column
            for column in (
                "acquired", "classified", "selected", "submitted", "failed"
            )
            if column in history.columns
        ]
        if numeric_columns:
            st.bar_chart(history.set_index("run_id")[numeric_columns])
