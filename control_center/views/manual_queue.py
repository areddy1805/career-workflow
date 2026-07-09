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
    update_manual_job,
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
            status_filter = st.selectbox(
                "Queue Status",
                ["ALL", *MANUAL_JOB_STATUSES],
            )
            visible = jobs if status_filter == "ALL" else jobs.loc[
                jobs["status"].eq(status_filter)
            ]

            st.download_button(
                "Export Tracked Jobs CSV",
                data=dataframe_to_csv_bytes(visible),
                file_name="career_workflow_manual_jobs.csv",
                mime="text/csv",
                disabled=visible.empty,
            )
            st.dataframe(visible, use_container_width=True, hide_index=True)

            if not visible.empty:
                selected_id = st.selectbox(
                    "Job ID",
                    visible["id"].astype(int).tolist(),
                )
                selected = visible.loc[visible["id"].eq(selected_id)].iloc[0]

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

                with st.expander("Edit Job"):
                    with st.form(f"edit_manual_job_{selected_id}"):
                        e1, e2 = st.columns(2)
                        edit_title = e1.text_input(
                            "Title", value=str(selected.get("title") or "")
                        )
                        edit_company = e2.text_input(
                            "Company", value=str(selected.get("company") or "")
                        )
                        edit_location = e1.text_input(
                            "Location", value=str(selected.get("location") or "")
                        )
                        source_value = str(selected.get("source") or "Other")
                        source_index = (
                            MANUAL_JOB_SOURCES.index(source_value)
                            if source_value in MANUAL_JOB_SOURCES
                            else MANUAL_JOB_SOURCES.index("Other")
                        )
                        edit_source = e2.selectbox(
                            "Source",
                            MANUAL_JOB_SOURCES,
                            index=source_index,
                        )
                        edit_url = st.text_input(
                            "Job URL", value=str(selected.get("source_url") or "")
                        )
                        priorities = ["", "TIER_A", "TIER_B", "TIER_C"]
                        priority_value = str(selected.get("priority") or "")
                        edit_priority = st.selectbox(
                            "Priority",
                            priorities,
                            index=priorities.index(priority_value)
                            if priority_value in priorities else 0,
                        )
                        edit_notes = st.text_area(
                            "Notes", value=str(selected.get("notes") or "")
                        )

                        if st.form_submit_button("Save Changes"):
                            try:
                                update_manual_job(
                                    int(selected_id),
                                    title=edit_title,
                                    company=edit_company,
                                    location=edit_location,
                                    source=edit_source,
                                    source_url=edit_url,
                                    priority=edit_priority,
                                    notes=edit_notes,
                                )
                                st.rerun()
                            except ValueError as error:
                                st.error(str(error))

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

            if "url" in queue.columns:
                actionable = queue.loc[
                    queue["url"].fillna("").astype(str).str.strip().ne("")
                ]
                if not actionable.empty:
                    selected_index = st.selectbox(
                        "External Action",
                        actionable.index.tolist(),
                        format_func=lambda idx: (
                            f"{actionable.loc[idx].get('title', '')} — "
                            f"{actionable.loc[idx].get('company', '')}"
                        ),
                    )
                    st.link_button(
                        "Open External Application",
                        str(actionable.loc[selected_index, "url"]),
                    )
