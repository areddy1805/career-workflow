from nicegui import ui
import pandas as pd

class DataTable:
    def __init__(self, data: pd.DataFrame | list[dict], title: str = "", classes: str = "", table_id: str = ""):
        self.data = data
        self.table_id = table_id or "default_table"
        self.grid = None

        with ui.column().classes(f"w-full self-stretch {classes} gap-2 min-w-0 max-w-full"):
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
            with ui.row().classes("self-stretch justify-between items-center flex-wrap gap-2"):
                self.search = ui.input(placeholder="Search...").classes("flex-1 min-w-[120px] max-w-[256px]").props('dense outlined clearable').on('update:model-value', self._on_search)
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
                    'width': 150,
                    'minWidth': 100,
                    'filter': True,
                    'sortable': True,
                    'resizable': True,
                },
                'onGridReady': f'''(params) => {{
                    const state = localStorage.getItem('agGridState_{self.table_id}');
                    if (state) {{
                        params.api.applyColumnState({{ state: JSON.parse(state), applyOrder: true }});
                    }}
                }}''',
                'onColumnMoved': f'''(params) => {{
                    const state = params.api.getColumnState();
                    localStorage.setItem('agGridState_{self.table_id}', JSON.stringify(state));
                }}''',
                'onColumnResized': f'''(params) => {{
                    if (params.finished) {{
                        const state = params.api.getColumnState();
                        localStorage.setItem('agGridState_{self.table_id}', JSON.stringify(state));
                    }}
                }}''',
                'onSortChanged': f'''(params) => {{
                    const state = params.api.getColumnState();
                    localStorage.setItem('agGridState_{self.table_id}', JSON.stringify(state));
                }}''',
            }).classes("w-full h-full flex-grow min-h-[200px] overflow-hidden ag-theme-balham-dark")

    def _on_search(self, e):
        if self.grid:
            self.grid.run_grid_method('setQuickFilter', e.value)

    def _export(self):
        if self.grid:
            self.grid.run_grid_method('exportDataAsCsv')

    def _fit(self):
        if self.grid:
            self.grid.run_grid_method('sizeColumnsToFit')
