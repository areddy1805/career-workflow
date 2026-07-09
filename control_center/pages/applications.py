from __future__ import annotations

import pandas as pd
import streamlit as st

from control_center.components import empty_state, page_header
from control_center.data import (
    LIFECYCLE_ORDER,
    read_application_events,
    read_applications,
)
from control_center.export import dataframe_to_csv_bytes


def render() -> None:
    page_header(
        "Applications",
        "Application execution state and recruiting lifecycle history.",
    )

    applications = read_applications()
    if applications.empty:
        empty_state("No applications found in the ledger.")
        return

    filters = st.columns(4)

    lifecycle = filters[0].selectbox(
        "Lifecycle",
        options=["ALL", *LIFECYCLE_ORDER],
    )

    companies = [
        "ALL",
        *sorted(
            value
            for value in applications["company"].dropna().astype(str).unique()
            if value
        ),
    ]
    company = filters[1].selectbox("Company", companies)

    priorities = [
        "ALL",
        *sorted(
            value
            for value in applications["priority"].dropna().astype(str).unique()
            if value
        ),
    ]
    priority = filters[2].selectbox("Priority", priorities)

    minimum_score = filters[3].number_input(
        "Minimum Score",
        min_value=0,
        max_value=100,
        value=0,
    )

    filtered = applications.copy()

    if lifecycle != "ALL":
        filtered = filtered.loc[
            filtered["lifecycle_stage"]
            .fillna("UNKNOWN")
            .astype(str)
            .str.upper()
            .eq(lifecycle)
        ]

    if company != "ALL":
        filtered = filtered.loc[filtered["company"].eq(company)]

    if priority != "ALL":
        filtered = filtered.loc[filtered["priority"].eq(priority)]

    scores = pd.to_numeric(filtered["score"], errors="coerce").fillna(0)
    filtered = filtered.loc[scores >= minimum_score]

    st.metric("Visible Applications", len(filtered))

    display_columns = [
        column
        for column in (
            "job_id", "title", "company", "location", "score",
            "priority", "subtrack", "source", "status",
            "lifecycle_stage", "applied_at", "last_updated_at",
        )
        if column in filtered.columns
    ]
    visible = filtered[display_columns]

    st.download_button(
        "Export Visible Applications CSV",
        data=dataframe_to_csv_bytes(visible),
        file_name="career_workflow_applications.csv",
        mime="text/csv",
        disabled=visible.empty,
    )

    st.dataframe(
        visible,
        use_container_width=True,
        hide_index=True,
    )

    if filtered.empty:
        return

    st.subheader("Application Detail")
    job_ids = filtered["job_id"].astype(str).tolist()
    selected_job_id = st.selectbox("Job ID", options=job_ids)

    selected = filtered.loc[
        filtered["job_id"].astype(str).eq(selected_job_id)
    ].iloc[0]

    left, right = st.columns(2)
    with left:
        st.json({
            "title": selected.get("title"),
            "company": selected.get("company"),
            "location": selected.get("location"),
            "score": selected.get("score"),
            "priority": selected.get("priority"),
            "subtrack": selected.get("subtrack"),
        })

    with right:
        st.json({
            "local_status": selected.get("status"),
            "server_status": selected.get("server_status"),
            "lifecycle_stage": selected.get("lifecycle_stage"),
            "applied_at": selected.get("applied_at"),
            "last_updated_at": selected.get("last_updated_at"),
            "last_error": selected.get("last_error"),
        })

    events = read_application_events(selected_job_id)
    if not events.empty:
        st.subheader("Status History")
        st.dataframe(events, use_container_width=True, hide_index=True)
