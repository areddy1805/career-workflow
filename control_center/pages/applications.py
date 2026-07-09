from __future__ import annotations

import pandas as pd
import streamlit as st

from control_center.data import (
    LIFECYCLE_ORDER,
    read_application_events,
    read_applications,
)


def render() -> None:
    st.title("Applications")

    st.caption("Application execution state and recruiting lifecycle history.")

    applications = read_applications()

    if applications.empty:
        st.info("No applications found in the ledger.")
        return

    filter_columns = st.columns(4)

    lifecycle = filter_columns[0].selectbox(
        "Lifecycle",
        options=[
            "ALL",
            *LIFECYCLE_ORDER,
        ],
    )

    company_options = [
        "ALL",
        *sorted(
            value
            for value in applications["company"].dropna().astype(str).unique()
            if value
        ),
    ]

    company = filter_columns[1].selectbox(
        "Company",
        options=company_options,
    )

    priority_options = [
        "ALL",
        *sorted(
            value
            for value in applications["priority"].dropna().astype(str).unique()
            if value
        ),
    ]

    priority = filter_columns[2].selectbox(
        "Priority",
        options=priority_options,
    )

    minimum_score = filter_columns[3].number_input(
        "Minimum Score",
        min_value=0,
        max_value=100,
        value=0,
    )

    filtered = applications.copy()

    if lifecycle != "ALL":
        filtered = filtered[
            filtered["lifecycle_stage"].fillna("UNKNOWN").astype(str).str.upper()
            == lifecycle
        ]

    if company != "ALL":
        filtered = filtered[filtered["company"] == company]

    if priority != "ALL":
        filtered = filtered[filtered["priority"] == priority]

    if "score" in filtered.columns:
        numeric_score = pd.to_numeric(
            filtered["score"],
            errors="coerce",
        ).fillna(0)

        filtered = filtered[numeric_score >= minimum_score]

    st.metric(
        "Visible Applications",
        len(filtered),
    )

    display_columns = [
        column
        for column in (
            "job_id",
            "title",
            "company",
            "location",
            "score",
            "priority",
            "subtrack",
            "source",
            "status",
            "lifecycle_stage",
            "applied_at",
            "last_updated_at",
        )
        if column in filtered.columns
    ]

    st.dataframe(
        filtered[display_columns],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Application Detail")

    job_ids = filtered["job_id"].astype(str).tolist()

    if not job_ids:
        st.info("No applications match the current filters.")
        return

    selected_job_id = st.selectbox(
        "Job ID",
        options=job_ids,
    )

    selected = filtered[filtered["job_id"].astype(str) == selected_job_id].iloc[0]

    detail_columns = st.columns(2)

    with detail_columns[0]:
        st.write(
            {
                "title": selected.get("title"),
                "company": selected.get("company"),
                "location": selected.get("location"),
                "score": selected.get("score"),
                "priority": selected.get("priority"),
                "subtrack": selected.get("subtrack"),
            }
        )

    with detail_columns[1]:
        st.write(
            {
                "local_status": selected.get("status"),
                "server_status": selected.get("server_status"),
                "lifecycle_stage": selected.get("lifecycle_stage"),
                "applied_at": selected.get("applied_at"),
                "last_updated_at": selected.get("last_updated_at"),
                "last_error": selected.get("last_error"),
            }
        )

    events = read_application_events(selected_job_id)

    if not events.empty:
        st.subheader("Status History")

        st.dataframe(
            events,
            use_container_width=True,
            hide_index=True,
        )
