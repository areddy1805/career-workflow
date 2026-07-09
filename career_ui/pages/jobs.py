from nicegui import ui
from career_ui.shell import shell
from career_ui.components import page_header,section,dataframe_table,empty_state
from career_ui.services.control_center import read_applications
@ui.page('/jobs')
def page():
    shell('/jobs')
    with ui.column().classes('cw-content gap-5'):
        page_header('WORKSPACE','Jobs','Search, filter, and inspect the job portfolio captured by the workflow.')
        frame=read_applications()
        if frame.empty: empty_state('No job records available','Run acquisition or import jobs first.'); return
        search=ui.input(placeholder='Search title, company, location…').props('outlined dense clearable').classes('w-full max-w-xl')
        table_host=ui.column().classes('w-full')
        def render():
            table_host.clear(); f=frame
            q=(search.value or '').strip().lower()
            if q:
                cols=[c for c in ('title','company','location','subtrack','priority') if c in f.columns]
                mask=f[cols].fillna('').astype(str).apply(lambda r:r.str.lower().str.contains(q,regex=False).any(),axis=1); f=f[mask]
            display=[c for c in ('job_id','title','company','location','score','priority','subtrack','source','status') if c in f.columns]
            with table_host: dataframe_table(f[display],pagination=25)
        search.on_value_change(lambda _:render()); render()
