"""
Menú principal interactivo
"""
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

try:
    import questionary
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("Error: Faltan dependencias. Ejecutar: pip install rich questionary")
    raise

from config.menu_data import MENU_DATA

if TYPE_CHECKING:
    from core.engine import BackgroundEngine
    from ui.dashboard import Dashboard


class MainMenu:
    """Menú principal interactivo"""
    
    def __init__(self, engine: "BackgroundEngine", dashboard_class: type):
        self.engine = engine
        self.dashboard_class = dashboard_class
        self.console = Console()
        self.current_target = "localhost"
        
        # Estilo Questionary
        self.custom_style = questionary.Style([
            ('qmark', 'fg:cyan bold'),
            ('question', 'fg:white bold'),
            ('answer', 'fg:green bold'),
            ('pointer', 'fg:cyan bold'),
            ('highlighted', 'fg:cyan bold'),
            ('selected', 'fg:green'),
            ('separator', 'fg:gray'),
            ('instruction', 'fg:gray'),
        ])

    def get_header(self) -> Panel:
        """Crear header del menú"""
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="right")
        grid.add_row(
            Text(f"🚀 IT-OPS CLI PRO | Target: [bold cyan]{self.current_target}[/bold cyan]", style="white"),
            Text(f"Jobs Activos: {len([j for j in self.engine.get_all_jobs() if j['status'] == 'RUNNING'])}", style="yellow")
        )
        return Panel(grid, border_style="blue")

    def change_target(self) -> None:
        """Cambiar equipo target"""
        new_target = questionary.text(
            "Ingresa el nuevo Hostname/IP target:",
            style=self.custom_style
        ).ask()
        if new_target:
            self.current_target = new_target.upper()

    def launch_task(self) -> None:
        """Lanzar una nueva tarea"""
        # Seleccionar categoría
        cat = questionary.select(
            "Selecciona Categoría:",
            choices=list(MENU_DATA.keys()) + ["⬅️ Volver"],
            style=self.custom_style
        ).ask()

        if cat == "⬅️ Volver" or not cat:
            return

        # Seleccionar playbook
        options = MENU_DATA[cat]
        choice = questionary.select(
            f"Lanzar tarea en {self.current_target}:",
            choices=[o[0] for o in options] + ["⬅️ Volver"],
            style=self.custom_style
        ).ask()

        if choice == "⬅️ Volver" or not choice:
            return

        # Encontrar el path del playbook
        playbook_path = next(o[1] for o in options if o[0] == choice)
        
        # Lanzar!
        job_id = self.engine.launch_playbook(playbook_path, self.current_target)
        self.console.print(f"[bold green]✔ Tarea lanzada con ID: {job_id}[/bold green]")
        time.sleep(1)

    def show_dashboard(self) -> None:
        """Mostrar dashboard de tareas"""
        dashboard = self.dashboard_class(self.engine)
        dashboard.show_live()

    def run(self) -> None:
        """Ejecutar menú principal"""
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.console.print(self.get_header())
            
            action = questionary.select(
                "¿Qué deseas hacer?",
                choices=[
                    "🚀 Lanzar Nueva Tarea",
                    "📊 Ver Dashboard de Tareas (Segundo Plano)",
                    "🎯 Cambiar Equipo Target",
                    "❌ Salir"
                ],
                style=self.custom_style
            ).ask()

            if action == "🚀 Lanzar Nueva Tarea":
                self.launch_task()
            elif action == "📊 Ver Dashboard de Tareas (Segundo Plano)":
                self.show_dashboard()
            elif action == "🎯 Cambiar Equipo Target":
                self.change_target()
            elif action == "❌ Salir" or not action:
                break
