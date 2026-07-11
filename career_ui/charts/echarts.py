from nicegui import ui

class Chart:
    def __init__(self, options: dict, classes: str = "w-full h-64"):
        # Standard interactive options for all charts
        default_opts = {
            'tooltip': {
                'trigger': 'item',
                'backgroundColor': 'rgba(24, 24, 27, 0.9)', # var(--panel)
                'borderColor': 'rgba(63, 63, 70, 0.5)', # var(--border)
                'textStyle': {'color': '#e4e4e7', 'fontSize': 12, 'fontFamily': 'Inter, sans-serif'}
            },
            'toolbox': {
                'feature': {
                    'dataZoom': {'yAxisIndex': 'none'},
                    'restore': {},
                    'saveAsImage': {}
                },
                'iconStyle': {'borderColor': '#a1a1aa'}
            },
            'backgroundColor': 'transparent',
            'textStyle': {
                'fontFamily': 'Inter, sans-serif'
            }
        }
        
        # Merge options (simple top-level merge, for complex deep merges custom logic is needed if user passes these keys)
        merged = {**default_opts, **options}
        
        self.chart = ui.echart(merged).classes(classes)
        
    def update(self):
        self.chart.update()
