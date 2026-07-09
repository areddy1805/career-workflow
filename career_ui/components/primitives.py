from __future__ import annotations
from html import escape
from typing import Any, Mapping, Sequence
import pandas as pd
from nicegui import ui

GOOD={'SUCCESS','PASS','ONLINE','IDLE','HEALTHY','COMPLETED','APPLIED','READY','CLEAR'}
WARN={'RUNNING','PARTIAL','ORPHANED','PENDING','EXECUTION','DEGRADED','WARN','WARNING','CHECK','ACTION'}
BAD={'FAILED','FAIL','ERROR','UNHEALTHY','BLOCKED'}

def page_header(kicker:str,title:str,subtitle:str,status:str|None=None):
    with ui.row().classes('cw-page-head w-full items-end justify-between gap-4'):
        with ui.column().classes('gap-0'):
            ui.html(f'<div class="cw-kicker">{escape(kicker)}</div><div class="cw-title">{escape(title)}</div><div class="cw-subtitle">{escape(subtitle)}</div>')
        if status: status_badge(status)

def section(title:str,subtitle:str=''):
    ui.html(f'<div class="cw-section-head"><div><div class="cw-section-title">{escape(title)}</div><div class="cw-section-sub">{escape(subtitle)}</div></div></div>')

def metric_card(label:str,value:Any,note:str=''):
    with ui.card().classes('cw-card cw-metric cw-card-interactive w-full'):
        ui.html(f'<div class="cw-metric-label">{escape(str(label))}</div><div class="cw-metric-value">{escape(str(value))}</div><div class="cw-metric-note">{escape(str(note))}</div>')

def status_class(status:Any)->str:
    s=str(status or 'UNKNOWN').upper()
    return 'cw-good' if s in GOOD else 'cw-warn' if s in WARN else 'cw-bad' if s in BAD else 'cw-neutral'

def status_badge(status:Any):
    s=str(status or 'UNKNOWN').upper()
    ui.html(f'<span class="cw-status {status_class(s)}">{escape(s)}</span>')

def hero(title:str,body:str,status:str|None=None):
    with ui.card().classes('cw-card cw-hero w-full'):
        with ui.row().classes('w-full items-center justify-between gap-4'):
            ui.html(f'<div><div class="cw-hero-title">{escape(title)}</div><div class="cw-hero-copy">{escape(body)}</div></div>')
            if status: status_badge(status)

def callout(title:str,body:str):
    ui.html(f'<div class="cw-callout"><div class="cw-callout-title">{escape(title)}</div><div class="cw-callout-copy">{escape(body)}</div></div>')

def empty_state(title:str,body:str=''):
    ui.html(f'<div class="cw-empty"><div style="font-size:28px;color:#66758a">◇</div><div style="color:#dce4ef;font-weight:700;margin-top:9px">{escape(title)}</div><div style="font-size:11px;margin-top:6px">{escape(body)}</div></div>').classes('w-full')

def dataframe_table(frame:pd.DataFrame, *, row_key:str|None=None, pagination:int=20, on_select=None):
    if frame is None or frame.empty: empty_state('No records found'); return None
    clean=frame.copy().where(pd.notna(frame), None)
    cols=[{'name':c,'label':c.replace('_',' ').title(),'field':c,'sortable':True,'align':'left'} for c in clean.columns]
    table=ui.table(columns=cols,rows=clean.to_dict('records'),row_key=row_key or clean.columns[0],pagination=pagination).classes('cw-table w-full')
    table.props('flat dense separator=horizontal')
    if on_select:
        table.props('selection=single')
        table.on('selection', lambda e: on_select((e.args.get('rows') or [None])[0]))
    return table

def stage_rail(stages:Mapping[str,Any]|Sequence):
    items=list(stages.items()) if isinstance(stages,Mapping) else list(stages)
    with ui.card().classes('cw-card cw-stage-card w-full'):
        with ui.row().classes('cw-stage-wrap w-full justify-between no-wrap overflow-auto'):
            for name,state in items:
                s=str(state or 'PENDING').upper(); cls='good' if s in {'SUCCESS','DONE','COMPLETED','PASS'} else 'run' if s=='RUNNING' else 'bad' if s in {'FAILED','FAIL','ERROR'} else ''
                ui.html(f'<div class="cw-stage"><div class="cw-orb {cls}"></div><div class="cw-stage-name">{escape(str(name).replace("_"," ").title())}</div><div class="cw-stage-state">{escape(s)}</div></div>')

def funnel(items:Sequence[tuple[str,int]]):
    values=[int(v or 0) for _,v in items]; peak=max([1,*values])
    with ui.card().classes('cw-card cw-funnel-card w-full'):
        for name,value in items:
            v=int(value or 0); width=(v/peak*100) if v else 0; zero='cw-funnel-zero' if not v else ''
            ui.html(f'<div class="cw-funnel-row"><div class="cw-funnel-name">{escape(str(name))}</div><div class="cw-funnel-track"><div class="cw-funnel-fill {zero}" style="width:{width:.2f}%"></div></div><div class="cw-funnel-value">{v:,}</div></div>')
