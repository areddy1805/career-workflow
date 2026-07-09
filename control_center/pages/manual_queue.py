from __future__ import annotations

import streamlit as st

from control_center.data import read_manual_action_queue


def render() -> None:
    st.title("Manual Queue")

    st.caption("External application actions requiring manual processing.")

    queue = read_manual_action_queue()

    if queue.empty:
        st.info("No manual actions are currently queued.")
        return

    st.dataframe(
        queue,
        use_container_width=True,
        hide_index=True,
    )
