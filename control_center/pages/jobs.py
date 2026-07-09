from __future__ import annotations

import pandas as pd
import streamlit as st

from control_center.data import read_applications


def render() -> None:
    st.title("Jobs")
    st.caption("Browse durable job records currently known to the application ledger.")

    jobs = read_applications()
    if jobs.empty:
        st.info("No job records are currently available.")
        return

    controls = st.columns(4)
    search = controls[0].text_input("Search")
    minimum = controls[1].number_input("Minimum Score", 0, 100, 0)
    priorities = ["ALL", *sorted(v for v in jobs["priority"].dropna().astype(str).unique() if v)]
    priority = controls[2].selectbox("Priority", priorities)
    subtracks = ["ALL", *sorted(v for v in jobs["subtrack"].dropna().astype(str).unique() if v)]
    subtrack = controls[3].selectbox("Subtrack", subtracks)

    filtered = jobs.copy()
    if search.strip():
        needle = search.strip().lower()
        mask = (
            filtered["title"].fillna("").astype(str).str.lower().str.contains(needle, regex=False)
            | filtered["company"].fillna("").astype(str).str.lower().str.contains(needle, regex=False)
        )
        filtered = filtered.loc[mask]

    scores = pd.to_numeric(filtered["score"], errors="coerce").fillna(0)
    filtered = filtered.loc[scores >= minimum]
    if priority != "ALL":
        filtered = filtered.loc[filtered["priority"] == priority]
    if subtrack != "ALL":
        filtered = filtered.loc[filtered["subtrack"] == subtrack]

    columns = ["job_id", "title", "company", "location", "score", "priority", "subtrack", "source", "status", "lifecycle_stage"]
    st.metric("Visible Jobs", len(filtered))
    st.dataframe(filtered[[c for c in columns if c in filtered.columns]], use_container_width=True, hide_index=True)
