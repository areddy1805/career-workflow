from __future__ import annotations
import streamlit as st
from control_center.components import funnel, header, hero, section, stages
from control_center.data import application_summary, latest_run, run_history
from control_center.runner import refresh_process_state

def n(run,key):
    try:return int(run.get(key,(run.get("counts") or {}).get(key,0)) or 0)
    except:return 0

def render():
    state=refresh_process_state(); run=latest_run(); apps=application_summary()
    header("Command Center","A single operational view of discovery throughput, pipeline health, and recruiting outcomes.","CAREER WORKFLOW")
    rid=str(run.get("run_id") or run.get("_run_dir") or "No run").split("/")[-1]
    hero("Job search engine online",f"Latest run · {rid[-18:]} · {'Dry run' if run.get('dry_run',True) else 'Live'}",state.get("status","IDLE"))
    a,b,c,d,e,f=st.columns(6)
    a.metric("Acquired",f"{n(run,'acquired'):,}")
    b.metric("Classified",f"{n(run,'classified'):,}")
    c.metric("Selected",f"{n(run,'selected'):,}")
    d.metric("Applications",f"{apps.get('total',0):,}")
    e.metric("Interviews",f"{apps.get('interview',0):,}")
    f.metric("Offers",f"{apps.get('offer',0):,}")
    left,right=st.columns([1.05,.95],gap="large")
    with left:
        section("Pipeline activity","Latest artifact stage progression")
        if run.get("stages"): stages(run["stages"])
        else: st.info("No stage data available.")
    with right:
        section("Recruiting funnel","Current ledger lifecycle")
        funnel([("Applications",apps.get("total",0)),("Viewed",apps.get("viewed",0)),("Shortlisted",apps.get("shortlisted",0)),("Interview",apps.get("interview",0)),("Offer",apps.get("offer",0))])
    section("Execution snapshot","Active process and latest artifact")
    x,y,z,w=st.columns(4)
    x.metric("Process",state.get("status","IDLE")); y.metric("Artifact",run.get("status","—")); z.metric("Submitted",n(run,"submitted")); w.metric("Failed",n(run,"failed"))
    act=st.columns([1,1,5])
    if act[0].button("Open Pipeline",type="primary",width="stretch"):
        st.session_state["navigation_target"]="Pipeline"; st.rerun()
    if act[1].button("Refresh",width="stretch"): st.rerun()
    section("Recent execution history","Newest pipeline artifacts")
    hist=run_history(limit=8)
    if hist.empty: st.info("No run history found.")
    else: st.dataframe(hist,width="stretch",hide_index=True)
