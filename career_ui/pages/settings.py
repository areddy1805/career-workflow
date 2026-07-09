import pandas as pd
from nicegui import ui
from career_ui.shell import shell
from career_ui.components import page_header,section,dataframe_table
from career_ui.services.control_center import safe_settings,ledger_path,runs_path,manual_queue_path,MANUAL_JOBS_DB
@ui.page('/settings')
def page():
    shell('/settings')
    with ui.column().classes('cw-content gap-5'):
        page_header('SYSTEM','Settings','Read-only operational configuration and resolved storage paths.','READ ONLY')
        section('Operational configuration','Safe non-secret environment values')
        dataframe_table(pd.DataFrame([{'Setting':k,'Value':v or 'DEFAULT / NOT SET'} for k,v in safe_settings().items()]))
        section('Storage','Resolved local persistence paths')
        paths=[('Application Ledger',ledger_path()),('Run Artifacts',runs_path()),('Pipeline External Queue',manual_queue_path()),('Manual External Jobs',MANUAL_JOBS_DB)]
        dataframe_table(pd.DataFrame([{'Store':n,'Path':str(p),'Exists':p.exists()} for n,p in paths]))
        ui.label('Secret configuration is intentionally excluded from this interface.').classes('text-xs text-slate-500')
