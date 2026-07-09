from __future__ import annotations

import pandas as pd
import streamlit as st

from control_center.components import empty_state, page_header
from control_center.data import read_applications
from control_center.export import dataframe_to_csv_bytes


def render() -> None:
    page_header(
        "Jobs",
        "Browse and filter durable job records currently known to the application ledger.",
    )

    jobs = read_applications()
    if jobs.empty:
        empty_state("No job records are currently available.")
        return

    controls = st.columns(4)
    search = controls[0].text_input("Search")
    minimum = controls[1].number_input("Minimum Score", 0, 100, 0)

    priorities = [
        "ALL",
        *sorted(v for v in jobs["priority"].dropna().astype(str).unique() if v),
    ]
    priority = controls[2].selectbox("Priority", priorities)

    subtracks = [
        "ALL",
        *sorted(v for v in jobs["subtrack"].dropna().astype(str).unique() if v),
    ]
    subtrack = controls[3].selectbox("Subtrack", subtracks)

    filtered = jobs.copy()

    if search.strip():
        needle = search.strip().lower()
        mask = (
            filtered["title"].fillna("").astype(str).str.lower().str.contains(
                needle, regex=False
            )
            | filtered["company"].fillna("").astype(str).str.lower().str.contains(
                needle, regex=False
            )
        )
        filtered = filtered.loc[mask]

    scores = pd.to_numeric(filtered["score"], errors="coerce").fillna(0)
    filtered = filtered.loc[scores >= minimum]

    if priority != "ALL":
        filtered = filtered.loc[filtered["priority"] == priority]

    if subtrack != "ALL":
        filtered = filtered.loc[filtered["subtrack"] == subtrack]

    st.metric("Visible Jobs", len(filtered))

    columns = [
        "job_id", "title", "company", "location", "score",
        "priority", "subtrack", "source", "status", "lifecycle_stage",
    ]
    visible = filtered[[c for c in columns if c in filtered.columns]]

    st.download_button(
        "Export Visible Jobs CSV",
        data=dataframe_to_csv_bytes(visible),
        file_name="career_workflow_jobs.csv",
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

    st.subheader("Job Detail")
    selected_id = st.selectbox(
        "Job ID",
        filtered["job_id"].astype(str).tolist(),
    )
    selected = filtered.loc[
        filtered["job_id"].astype(str) == selected_id
    ].iloc[0]

    st.json({
        "job_id": selected.get("job_id"),
        "title": selected.get("title"),
        "company": selected.get("company"),
        "location": selected.get("location"),
        "score": selected.get("score"),
        "priority": selected.get("priority"),
        "subtrack": selected.get("subtrack"),
        "source": selected.get("source"),
        "local_status": selected.get("status"),
        "lifecycle_stage": selected.get("lifecycle_stage"),
    })
