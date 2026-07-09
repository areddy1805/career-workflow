from __future__ import annotations
import streamlit as st
from control_center.components import header, section, stages
from control_center.data import calculate_duration, latest_terminal_run, run_history
from control_center.runner import launch_pipeline,pipeline_is_running,read_pipeline_log,refresh_process_state

def render():
    state=refresh_process_state(); running=pipeline_is_running()
    header("Pipeline Control","Configure, launch, and inspect the staged application engine without leaving the control center.","EXECUTION")
    a,b,c,d,e=st.columns(5)
    a.metric("Process",state.get("status","IDLE")); b.metric("PID",state.get("pid") or "—"); c.metric("Mode","LIVE" if state.get("live") else "DRY RUN"); d.metric("Elapsed",calculate_duration(state.get("started_at"),state.get("completed_at"))); e.metric("Exit",state.get("exit_code") if state.get("exit_code") is not None else "—")
    left,right=st.columns([.78,1.22],gap="large")
    with left:
        section("Run configuration","Safety-first execution controls")
        with st.container(border=True):
            mode=st.segmented_control("Execution mode",["Dry Run","Live"],default="Dry Run",disabled=running)
            live=mode=="Live"
            limit=st.number_input("Application ceiling",1,1000,3 if live else 500,disabled=running)
            canary=False
            if live:
                canary=st.toggle("Canary · force one application",disabled=running)
                st.error("LIVE execution can submit real applications.")
                confirmed=st.checkbox("I understand this can submit real applications.",disabled=running)
            else:
                confirmed=True; st.info("Simulation mode. No applications will be submitted.")
            if st.button("Launch Live Run" if live else "Launch Dry Run",type="primary",width="stretch",disabled=running or not confirmed):
                try: launch_pipeline(live=live,max_applications=int(limit),canary=canary); st.rerun()
                except Exception as error: st.error(f"Launch failed: {error}")
            if st.button("Refresh Runtime State",width="stretch"): st.rerun()
    with right:
        section("Run progression","Latest completed artifact")
        latest=latest_terminal_run()
        if latest and latest.get("stages"): stages(latest["stages"])
        else: st.info("No completed stage summary available.")
        if latest:
            x,y,z,w=st.columns(4)
            counts=latest.get("counts") or {}
            x.metric("Acquired",latest.get("acquired",counts.get("acquired",0)))
            y.metric("Classified",latest.get("classified",counts.get("classified",0)))
            z.metric("Selected",latest.get("selected",counts.get("selected",0)))
            w.metric("Submitted",latest.get("submitted",0))
    if running:
        section("Live process output","Tail of the active launcher log")
        st.markdown('<div class="cw-console-head"><span class="cw-console-title">pipeline.log · live tail</span><span class="cw-status"><span class="cw-dot"></span>RUNNING</span></div>',unsafe_allow_html=True)
        log=read_pipeline_log()
        st.code(log or "Waiting for pipeline output…",language="text")
    else:
        section("Runtime","No active process")
        st.caption("Historical output remains available in Run Inspector. The pipeline log is shown here only while a process is active.")
    section("Run history","Completed and diagnostic artifacts")
    hist=run_history(limit=20)
    if hist.empty: st.info("No run history found.")
    else: st.dataframe(hist,width="stretch",hide_index=True)
