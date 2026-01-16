"""
Hub Menu Principal - TUI Interactivo
"""
import os
import questionary
from typing import TYPE_CHECKING
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from core.context import AppContext
from ui.dashboard import Dashboard
from ui.sections.targets import TargetsSection
from ui.sections.ad import ADSection
from ui.sections.windows import WindowsSection
from ui.sections.hardware import HardwareSection
from ui.sections.network import NetworkSection
from ui.sections.sccm import SCCMSection
from ui.sections.wlc import WLCSection
from ui.sections.monitoring import MonitoringSection
from ui.sections.logs import LogsSection
from ui.sections.settings import SettingsSection

if TYPE_CHECKING:
    from core.engine import BackgroundEngine


class HubMenu:
    """Menú principal del Hub TUI"""
    
    def __init__(self, engine: "BackgroundEngine"):
        self.engine = engine
        self.context = AppContext()
        self.console = Console()
        
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
        """Crear header del hub con estado visible"""
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="right")
        
        ctx_dict = self.context.to_dict()
        active_jobs = len([j for j in self.engine.get_all_jobs() if j['status'] == 'RUNNING'])
        
        grid.add_row(
            Text(f"🚀 IT-OPS CLI | Target: [bold cyan]{ctx_dict['target']}[/bold cyan]", style="white"),
            Text(f"Jobs: {active_jobs}", style="yellow")
        )
        grid.add_row(
            Text(f"Read-only: {ctx_dict['read_only_mode']} | Check: {ctx_dict['check_mode']}", style="dim"),
            Text(f"Último: {ctx_dict['last_result']}", style="dim")
        )
        
        return Panel(grid, border_style="blue")
    
    def run(self) -> None:
        """Ejecutar hub principal"""
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.console.print(self.get_header())
            
            action = questionary.select(
                "¿Qué deseas hacer?",
                choices=[
                    "🎯 Targets",
                    "🔐 AD",
                    "📊 SCCM",
                    "📶 WiFi / Network",
                    "💻 Windows / Software",
                    "🔧 Hardware / Diagnostics",
                    "🌐 WLC",
                    "📈 Monitoreo",
                    "📋 Logs / Reportes",
                    "⚙️ Settings",
                    "📊 Dashboard de Tareas",
                    "❌ Exit"
                ],
                style=self.custom_style
            ).ask()
            
            if not action or action == "❌ Exit":
                # Guardar contexto antes de salir
                self.context.save(persist=True)
                break
            
            try:
                if action == "🎯 Targets":
                    section = TargetsSection(self.context)
                    section.run()
                elif action == "🔐 AD":
                    section = ADSection(self.context, self.engine)
                    section.run()
                elif action == "📊 SCCM":
                    section = SCCMSection(self.context, self.engine)
                    section.run()
                elif action == "📶 WiFi / Network":
                    section = NetworkSection(self.context, self.engine)
                    section.run()
                elif action == "💻 Windows / Software":
                    section = WindowsSection(self.context, self.engine)
                    section.run()
                elif action == "🔧 Hardware / Diagnostics":
                    section = HardwareSection(self.context, self.engine)
                    section.run()
                elif action == "🌐 WLC":
                    section = WLCSection(self.context, self.engine)
                    section.run()
                elif action == "📈 Monitoreo":
                    section = MonitoringSection(self.context, self.engine)
                    section.run()
                elif action == "📋 Logs / Reportes":
                    section = LogsSection(self.context, self.engine)
                    section.run()
                elif action == "⚙️ Settings":
                    section = SettingsSection(self.context, self.engine)
                    section.run()
                elif action == "📊 Dashboard de Tareas":
                    dashboard = Dashboard(self.engine)
                    dashboard.show_live()
            except KeyboardInterrupt:
                # Permitir salir con Ctrl+C
                continue
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                input("\nPresiona Enter para continuar...")
