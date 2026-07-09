from nicegui import ui
from career_ui.shell import shell
from career_ui.components import page_header,metric_card,section,dataframe_table,empty_state
from career_ui.services.control_center import read_manual_jobs,add_manual_job,update_manual_job_status,MANUAL_JOB_SOURCES
@ui.page('/manual-queue')
def page():
    shell('/manual-queue')
    with ui.column().classes('cw-content gap-5'):
        page_header('WORK QUEUE','Manual Queue','Capture external opportunities and move them through a deliberate application workflow.')
        host=ui.column().classes('w-full gap-4')
        def refresh():
            host.clear(); f=read_manual_jobs()
            with host:
                with ui.element('div').classes('cw-grid-4 w-full'):
                    metric_card('Total',len(f),'external jobs'); metric_card('To Apply',int((f.status=='TO_APPLY').sum()) if not f.empty else 0,'actionable'); metric_card('Applied',int((f.status=='APPLIED').sum()) if not f.empty else 0,'completed'); metric_card('Discovered',int((f.status=='DISCOVERED').sum()) if not f.empty else 0,'triage')
                if f.empty: empty_state('Manual queue is empty'); return
                display=[c for c in ('id','title','company','location','source','status','priority','updated_at') if c in f.columns]; dataframe_table(f[display],pagination=20)
                with ui.row().classes('items-end gap-3'):
                    jid=ui.number('Job ID',min=1).props('outlined dense'); status=ui.select(['SHORTLISTED','TO_APPLY','APPLIED','SKIPPED','EXPIRED'],label='Move to').props('outlined dense')
                    def move():
                        if not jid.value or not status.value:return
                        update_manual_job_status(int(jid.value),status.value); ui.notify('Status updated',type='positive'); refresh()
                    ui.button('Update Status',on_click=move).props('color=primary unelevated')
        with ui.expansion('Add external job',icon='add_circle').classes('cw-card w-full'):
            with ui.grid(columns=2).classes('w-full gap-3 p-3'):
                title=ui.input('Title'); company=ui.input('Company'); location=ui.input('Location'); source=ui.select(list(MANUAL_JOB_SOURCES),label='Source',value='LinkedIn'); url=ui.input('Source URL'); priority=ui.select(['P1','P2','P3'],label='Priority',value='P2'); notes=ui.textarea('Notes').classes('col-span-2')
            def add():
                try: add_manual_job(title=title.value or '',company=company.value or '',location=location.value or '',source=source.value,source_url=url.value or '',priority=priority.value,notes=notes.value or ''); ui.notify('Job added',type='positive'); refresh()
                except Exception as e: ui.notify(str(e),type='negative')
            ui.button('Add Job',on_click=add).props('color=primary unelevated').classes('m-3')
        refresh()
