from __future__ import annotations

import streamlit as st

from control_center.pages.analytics import render as render_analytics
from control_center.pages.applications import render as render_applications
from control_center.pages.dashboard import render as render_dashboard
from control_center.pages.jobs import render as render_jobs
from control_center.pages.manual_queue import render as render_manual_queue
from control_center.pages.pipeline import render as render_pipeline
from control_center.pages.review_queue import render as render_review_queue
from control_center.pages.settings import render as render_settings

st.set_page_config(
    page_title="Career Workflow",
    layout="wide",
    initial_sidebar_state="expanded",
)


PAGES = {
    "Dashboard": render_dashboard,
    "Pipeline": render_pipeline,
    "Jobs": render_jobs,
    "Applications": render_applications,
    "Manual Queue": render_manual_queue,
    "Review Queue": render_review_queue,
    "Analytics": render_analytics,
    "Settings": render_settings,
}


def main() -> None:
    st.sidebar.title("Career Workflow")

    selected_page = st.sidebar.radio(
        "Navigation",
        options=list(PAGES.keys()),
    )

    renderer = PAGES[selected_page]

    try:
        renderer()
    except Exception as error:
        st.error(f"Page rendering failed: {type(error).__name__}: {error}")
        st.exception(error)


if __name__ == "__main__":
    main()
