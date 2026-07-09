import html
from nicegui import ui
from career_ui.shell import shell
from career_ui.components import page_header,metric_card,section,stage_rail,dataframe_table,hero,callout
from career_ui.services.control_center import refresh_process_state,pipeline_is_running,read_pipeline_log,launch_pipeline,latest_terminal_run,run_history,calculate_duration

def _run_projection(frame):
    if frame is None or frame.empty:return frame
    cols=[c for c in ('run_id','status','dry_run','max_applications','acquired','classified','selected','submitted','failed','started_at') if c in frame.columns]
    return frame[cols]

@ui.page('/pipeline')
def page():
    shell('/pipeline')
    with ui.column().classes('cw-content gap-5'):
        state=refresh_process_state(); process=str(state.get('status','IDLE')).upper()
        page_header('OPERATE','Pipeline Control','Configure, execute, and observe the application engine while preserving process truth.',process)
        hero('Mission control','Dry run is the default safety boundary. Live mode requires explicit confirmation. Process telemetry and terminal artifacts are displayed separately.',process)
        metrics=ui.element('div').classes('cw-grid-4 w-full')
        with ui.element('div').classes('cw-split w-full'):
            with ui.column().classes('gap-3'):
                section('Artifact execution map','Latest terminal artifact · historical truth')
                latest=latest_terminal_run(); stage_rail(latest.get('stages') or {'preflight':'PENDING','acquisition':'PENDING','classification':'PENDING','selection':'PENDING','application':'PENDING','reconciliation':'PENDING','report':latest.get('status','UNKNOWN')})
            with ui.card().classes('cw-card p-5 gap-4'):
                section('Run configuration','Safety-first execution controls')
                mode=ui.toggle(['Dry Run','Live'],value='Dry Run').props('spread')
                limit=ui.number('Application ceiling',value=500,min=1,max=1000).classes('w-full')
                canary=ui.switch('Canary · one live application')
                confirm=ui.checkbox('I understand LIVE mode can submit applications')
                def mode_change():
                    live=mode.value=='Live'; canary.set_visibility(live); confirm.set_visibility(live); limit.value=3 if live else 500
                mode.on_value_change(lambda _:mode_change()); mode_change()
                async def launch():
                    live=mode.value=='Live'
                    if live and not confirm.value: ui.notify('Live confirmation is required',type='warning'); return
                    try: launch_pipeline(live=live,max_applications=int(limit.value),canary=bool(canary.value)); ui.notify('Pipeline launched',type='positive'); render_state()
                    except Exception as e: ui.notify(str(e),type='negative')
                ui.button('Launch Pipeline',icon='rocket_launch',on_click=launch).props('color=primary unelevated').classes('w-full')
                ui.button('Refresh State',icon='refresh',on_click=lambda:render_state()).props('outline').classes('w-full')
        section('Live process telemetry','Launcher-owned state only')
        log_box=ui.html('').classes('cw-console w-full')
        def render_state():
            metrics.clear(); state=refresh_process_state(); running=pipeline_is_running()
            with metrics:
                metric_card('Process',state.get('status','IDLE'),'live launcher state'); metric_card('PID',state.get('pid') or '—','process owner'); metric_card('Mode','LIVE' if state.get('live') else 'DRY RUN','execution safety'); metric_card('Elapsed',calculate_duration(state.get('started_at'),state.get('completed_at')),'wall clock')
            content=read_pipeline_log() if running else 'No active process. Historical output is available in Run Inspector.'
            log_box.set_content(f'<pre style="margin:0;white-space:pre-wrap">{html.escape(content)}</pre>')
        section('Live output','Active launcher log · refreshed every two seconds while this page is open')
        section('Run history','Recent execution artifacts')
        dataframe_table(_run_projection(run_history(20)),pagination=10)
        render_state(); ui.timer(2.0,render_state)
