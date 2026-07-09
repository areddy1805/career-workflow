from __future__ import annotations
import streamlit as st
from control_center.theme import apply_theme
from control_center.views.analytics import render as render_analytics
from control_center.views.applications import render as render_applications
from control_center.views.dashboard import render as render_dashboard
from control_center.views.health import render as render_health
from control_center.views.jobs import render as render_jobs
from control_center.views.manual_queue import render as render_manual_queue
from control_center.views.pipeline import render as render_pipeline
from control_center.views.review_queue import render as render_review_queue
from control_center.views.run_inspector import render as render_run_inspector
from control_center.views.settings import render as render_settings

st.set_page_config(page_title="Career Workflow", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
apply_theme()

PAGES={"Command Center":render_dashboard,"Pipeline":render_pipeline,"Run Inspector":render_run_inspector,"Jobs":render_jobs,"Applications":render_applications,"Manual Queue":render_manual_queue,"Review Queue":render_review_queue,"Analytics":render_analytics,"System Health":render_health,"Settings":render_settings}
ALIASES={"Dashboard":"Command Center"}

def main():
    st.sidebar.markdown('<div class="cw-brand"><div class="cw-mark">CW</div><div class="cw-brand-title">Career Workflow</div><div class="cw-brand-sub">AI Job Operations</div></div>',unsafe_allow_html=True)
    target=st.session_state.pop("navigation_target",None)
    target=ALIASES.get(target,target)
    if target in PAGES: st.session_state["main_navigation"]=target
    selected=st.sidebar.radio("Workspace",list(PAGES),key="main_navigation",label_visibility="collapsed")
    st.sidebar.markdown('<div class="cw-footer">LOCAL CONTROL CENTER<br>ARTIFACT-DRIVEN STATE</div>',unsafe_allow_html=True)
    try: PAGES[selected]()
    except Exception as error:
        st.error(f"Page rendering failed: {type(error).__name__}: {error}")
        with st.expander("Technical detail"): st.exception(error)
if __name__=="__main__": main()
