from __future__ import annotations

import pandas as pd
import streamlit as st

from control_center.components import page_header
from control_center.run_inspector import (
    available_runs,
    inspect_run,
    read_text_artifact,
)


TEXT_SUFFIXES = {".json", ".txt", ".log", ".md", ".csv"}


def render() -> None:
    page_header(
        "Run Inspector",
        "Inspect pipeline run state, result payloads, and generated artifacts.",
    )

    runs = available_runs()
    if not runs:
        st.info("No run artifacts are available.")
        return

    selected = st.selectbox("Run", runs)
    payload = inspect_run(selected)

    if not payload:
        st.error("The selected run could not be loaded.")
        return

    state_tab, result_tab, files_tab = st.tabs(
        ["Run State", "Result", "Artifacts"]
    )

    with state_tab:
        state = payload.get("state", {})
        if state:
            st.json(state)
        else:
            st.info("No run.json state payload found.")

    with result_tab:
        result = payload.get("result", {})
        if result:
            st.json(result)
        else:
            st.info("No result.json payload found.")

    with files_tab:
        files = payload.get("files", [])
        if not files:
            st.info("No artifact files found.")
            return

        frame = pd.DataFrame(files)
        st.dataframe(frame, use_container_width=True, hide_index=True)

        readable = [
            row["relative_path"]
            for row in files
            if row["suffix"] in TEXT_SUFFIXES
        ]
        if readable:
            selected_file = st.selectbox("Preview Artifact", readable)
            content = read_text_artifact(selected, selected_file)
            st.code(content or "Artifact is empty.", language="text")
