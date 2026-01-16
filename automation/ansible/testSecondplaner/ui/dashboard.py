"""
Dashboard unificado para visualización de jobs en tiempo real
"""
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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.engine import BackgroundEngine


class Dashboard:
    """Dashboard en tiempo real para monitorear jobs"""
    
    def __init__(self, engine: "BackgroundEngine"):
        self.engine = engine
        self.console = Console()
        self.selected_job_id: str | None = None

    def make_layout(self) -> Layout:
        """Crear layout del dashboard"""
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
        """Crear header del dashboard"""
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right")
        grid.add_row(
            Text("IT-OPS CLI | Background Execution System", style="bold white"),
            Text(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="dim")
        )
        return Panel(grid, border_style="blue", box=box.SIMPLE)

    def get_footer(self) -> Panel:
        """Crear footer con atajos"""
        shortcuts = [
            ("[bold cyan]Q[/bold cyan] Salir", "white"),
            ("[bold cyan]C[/bold cyan] Cancelar Job", "white"),
            ("[bold cyan]V[/bold cyan] Ver Logs", "white"),
            ("[bold cyan]L[/bold cyan] Limpiar Historial", "white")
        ]
        columns = Columns([Text.from_markup(f"{s[0]}") for s in shortcuts], expand=True)
        return Panel(columns, box=box.SIMPLE)

    def get_jobs_table(self) -> Panel:
        """Crear tabla de jobs"""
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
        """Crear panel de logs"""
        jobs = self.engine.get_all_jobs()
        log_content = "Seleccione un trabajo para ver logs..."
        
        if jobs:
            # Mostrar logs del último job o del seleccionado
            job_to_show = next((j for j in jobs if j["id"] == self.selected_job_id), None)
            if not job_to_show:
                job_to_show = jobs[-1]
            
            logs = self.engine.get_job_output(job_to_show["id"])
            if logs:
                log_content = "\n".join(logs[-15:])  # Últimas 15 líneas
            else:
                log_content = "Esperando salida..."

        return Panel(
            Text(log_content, style="dim white", overflow="ellipsis"),
            title="[bold yellow] Live Logs [/bold yellow]",
            border_style="yellow"
        )

    def update_layout(self, layout: Layout) -> None:
        """Actualizar el layout con datos actuales"""
        layout["header"].update(self.get_header())
        layout["left"].update(self.get_jobs_table())
        layout["right"].update(self.get_logs_panel())
        layout["footer"].update(self.get_footer())

    def show_live(self) -> None:
        """Mostrar dashboard en tiempo real"""
        layout = self.make_layout()
        with Live(layout, refresh_per_second=4, screen=True) as live:
            try:
                while True:
                    self.update_layout(layout)
                    time.sleep(0.25)
            except KeyboardInterrupt:
                self.console.print("[yellow]Dashboard cerrado[/yellow]")
