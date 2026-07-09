from nicegui import ui
from career_ui.shell import shell
from career_ui.components import page_header,metric_card,section,stage_rail,funnel,dataframe_table,hero,callout
from career_ui.services.control_center import application_summary,latest_run,run_history,refresh_process_state,run_count,pipeline_is_running

def _run_projection(frame):
    if frame is None or frame.empty:return frame
    cols=[c for c in ('run_id','status','dry_run','max_applications','acquired','classified','selected','submitted','failed','started_at') if c in frame.columns]
    return frame[cols].copy()

@ui.page('/')
def page():
    shell('/')
    with ui.column().classes('cw-content gap-5'):
        state=refresh_process_state(); run=latest_run(); apps=application_summary(); process=str(state.get('status','IDLE')).upper(); artifact=str(run.get('status','UNKNOWN')).upper(); running=pipeline_is_running()
        page_header('OPERATIONS','Command Center','Live process truth, latest artifact throughput, conversion, and work requiring attention.',process)
        hero('Application engine overview','Live launcher state and immutable run artifacts are deliberately separated. Operate from Pipeline Control; inspect outcomes here.',process)
        with ui.element('div').classes('cw-grid-5 w-full'):
            metric_card('Process',process,'live launcher state')
            metric_card('Artifact',artifact,'latest run result')
            metric_card('Acquired',f"{run_count(run,'acquired'):,}",'latest artifact')
            metric_card('Selected',f"{run_count(run,'selected'):,}",'qualified opportunities')
            metric_card('Portfolio',f"{int(apps.get('total',0)):,}",'lifetime applications')
        if artifact=='ORPHANED' and not running:
            callout('Artifact requires attention','The latest run artifact is ORPHANED, but no live process owns it. Treat the artifact as historical state; use Run Inspector for evidence or Pipeline Control for a new execution.')
        section('Execution map','Latest artifact-backed stage progression · not live process state')
        stages=run.get('stages') or {'preflight':'PENDING','acquisition':'PENDING','classification':'PENDING','selection':'PENDING','application':'PENDING','reconciliation':'PENDING','report':run.get('status','UNKNOWN')}
        stage_rail(stages)
        with ui.element('div').classes('cw-grid-2 w-full'):
            with ui.column().classes('gap-3'):
                section('Application funnel','Portfolio lifecycle distribution')
                funnel([('Submitted',apps.get('submitted',apps.get('total',0))),('Viewed',apps.get('viewed',0)),('Shortlisted',apps.get('shortlisted',0)),('Interview',apps.get('interview',0)),('Offer',apps.get('offer',0))])
            with ui.column().classes('gap-3'):
                section('Recent runs','Compact execution history')
                dataframe_table(_run_projection(run_history(8)),pagination=8)
