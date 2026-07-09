from __future__ import annotations

import streamlit as st

from control_center.components import page_header
from control_center.data import read_manual_action_queue
from control_center.export import dataframe_to_csv_bytes
from control_center.manual_jobs import (
    MANUAL_JOB_SOURCES,
    MANUAL_JOB_STATUSES,
    add_manual_job,
    read_manual_jobs,
    update_manual_job_status,
)


def render() -> None:
    page_header(
        "Manual Queue",
        "Track externally discovered jobs and pipeline external-apply actions.",
    )

    tracker, actions = st.tabs(
        ["External Job Tracker", "Pipeline External Actions"]
    )

    with tracker:
        with st.expander("Add Job"):
            with st.form("add_manual_job", clear_on_submit=True):
                c1, c2 = st.columns(2)
                title = c1.text_input("Title *")
                company = c2.text_input("Company *")
                location = c1.text_input("Location")
                source = c2.selectbox("Source *", MANUAL_JOB_SOURCES)
                source_url = st.text_input("Job URL")
                priority = st.selectbox(
                    "Priority", ["", "TIER_A", "TIER_B", "TIER_C"]
                )
                notes = st.text_area("Notes")

                if st.form_submit_button("Add Job", type="primary"):
                    try:
                        add_manual_job(
                            title=title,
                            company=company,
                            location=location,
                            source=source,
                            source_url=source_url,
                            priority=priority,
                            notes=notes,
                        )
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))

        jobs = read_manual_jobs()
        if jobs.empty:
            st.info("No manual jobs have been added.")
        else:
            st.download_button(
                "Export Tracked Jobs CSV",
                data=dataframe_to_csv_bytes(jobs),
                file_name="career_workflow_manual_jobs.csv",
                mime="text/csv",
            )
            st.dataframe(jobs, use_container_width=True, hide_index=True)

            selected_id = st.selectbox(
                "Job ID",
                jobs["id"].astype(int).tolist(),
            )
            selected = jobs.loc[jobs["id"].eq(selected_id)].iloc[0]

            status_index = (
                MANUAL_JOB_STATUSES.index(selected["status"])
                if selected["status"] in MANUAL_JOB_STATUSES
                else 0
            )
            status = st.selectbox(
                "Status",
                MANUAL_JOB_STATUSES,
                index=status_index,
            )

            c1, c2, c3 = st.columns(3)

            if c1.button("Update Status", type="primary"):
                update_manual_job_status(int(selected_id), status)
                st.rerun()

            if c2.button("Mark Applied"):
                update_manual_job_status(int(selected_id), "APPLIED")
                st.rerun()

            if c3.button("Mark Skipped"):
                update_manual_job_status(int(selected_id), "SKIPPED")
                st.rerun()

            if selected.get("source_url"):
                st.link_button("Open Job", str(selected["source_url"]))

    with actions:
        queue = read_manual_action_queue()
        if queue.empty:
            st.info("No pipeline external-apply actions are queued.")
        else:
            st.download_button(
                "Export External Actions CSV",
                data=dataframe_to_csv_bytes(queue),
                file_name="career_workflow_external_actions.csv",
                mime="text/csv",
            )
            st.dataframe(queue, use_container_width=True, hide_index=True)
