from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns
from rich import box
from datetime import datetime
import time

class Dashboard:
    def __init__(self, engine):
        self.engine = engine
        self.console = Console()
        self.selected_job_id = None

    def make_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        return layout

    def get_header(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right")
        grid.add_row(
            Text("IT-OPS CLI | Background Execution System", style="bold white"),
            Text(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="dim")
        )
        return Panel(grid, style="bg:blue fg:white", box=box.SIMPLE)

    def get_footer(self) -> Panel:
        shortcuts = [
            ("[bold cyan]Q[/bold cyan] Salir", "white"),
            ("[bold cyan]C[/bold cyan] Cancelar Job", "white"),
            ("[bold cyan]V[/bold cyan] Ver Logs", "white"),
            ("[bold cyan]L[/bold cyan] Limpiar Historial", "white")
        ]
        columns = Columns([Text.from_markup(f"{s[0]}") for s in shortcuts], expand=True)
        return Panel(columns, box=box.SIMPLE)

    def get_jobs_table(self) -> Panel:
        table = Table(box=box.MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("ID", style="cyan", width=10)
        table.add_column("Playbook", style="bold white")
        table.add_column("Target", style="magenta")
        table.add_column("Estado", justify="center")
        table.add_column("Tiempo", justify="right")

        jobs = self.engine.get_all_jobs()
        for job in jobs:
            status = job["status"]
            style = "white"
            icon = "●"
            
            if status == "RUNNING":
                style = "yellow"
                icon = "⚙"
            elif status == "SUCCESS":
                style = "green"
                icon = "✔"
            elif status == "FAILED":
                style = "red"
                icon = "✘"
            elif status == "CANCELLED":
                style = "bright_black"
                icon = "🛑"

            table.add_row(
                job["id"],
                job["playbook"],
                job["target"],
                Text(f"{icon} {status}", style=style),
                job["duration"]
            )
        
        return Panel(table, title="[bold blue] Trabajos Activos [/bold blue]", border_style="blue")

    def get_logs_panel(self) -> Panel:
        # Por ahora mostramos los logs del último job o uno seleccionado
        jobs = self.engine.get_all_jobs()
        log_content = "Seleccione un trabajo para ver logs..."
        
        if jobs:
            last_job = jobs[-1]
            logs = self.engine.get_job_output(last_job["id"])
            if logs:
                log_content = "\n".join(logs[-15:]) # Últimas 15 líneas
            else:
                log_content = "Esperando salida..."

        return Panel(
            Text(log_content, style="dim white", overflow="ellipsis"),
            title="[bold yellow] Live Logs [/bold yellow]",
            border_style="yellow"
        )

    def update_layout(self, layout):
        layout["header"].update(self.get_header())
        layout["left"].update(self.get_jobs_table())
        layout["right"].update(self.get_logs_panel())
        layout["footer"].update(self.get_footer())

    def show_live(self):
        layout = self.make_layout()
        with Live(layout, refresh_per_second=4, screen=True) as live:
            try:
                while True:
                    self.update_layout(layout)
                    time.sleep(0.25)
            except KeyboardInterrupt:
                pass
