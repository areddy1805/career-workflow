from nicegui import ui
import pandas as pd

class DataTable:
    def __init__(self, data: pd.DataFrame | list[dict], title: str = "", classes: str = ""):
        self.data = data
        self.grid = None
        
        with ui.column().classes(f"w-full {classes} gap-2"):
            if title:
                ui.html(f'<div class="font-semibold text-sm mb-2" style="color:var(--text)">{title}</div>')
            
            if isinstance(data, pd.DataFrame):
                records = data.to_dict('records')
            else:
                records = data
                
            if not records:
                from career_ui.components.feedback import empty_state
                empty_state("No data available", "There are no records to display in this table.", icon="table_rows")
                return
            
            # Toolbar
            with ui.row().classes("w-full justify-between items-center"):
                self.search = ui.input(placeholder="Search...").classes("w-64").props('dense outlined clearable').on('update:model-value', self._on_search)
                with ui.row().classes("gap-2"):
                    ui.button("Export CSV", on_click=self._export).props('dense outline icon=download size=sm color=grey-8')
                    ui.button("Fit Columns", on_click=self._fit).props('dense outline icon=view_column size=sm color=grey-8')

            columns = [{"field": k, "sortable": True, "filter": True, "resizable": True} for k in records[0].keys()]
            
            self.grid = ui.aggrid({
                'columnDefs': columns,
                'rowData': records,
                'rowSelection': 'multiple',
                'animateRows': True,
                'suppressCellFocus': False,
                'defaultColDef': {
                    'flex': 1,
                    'minWidth': 100,
                    'filter': True,
                    'sortable': True,
                    'resizable': True,
                }
            }).classes("w-full h-96 ag-theme-balham-dark")

    def _on_search(self, e):
        if self.grid:
            self.grid.run_grid_method('setQuickFilter', e.value)
            
    def _export(self):
        if self.grid:
            self.grid.run_grid_method('exportDataAsCsv')

    def _fit(self):
        if self.grid:
            self.grid.run_grid_method('sizeColumnsToFit')
