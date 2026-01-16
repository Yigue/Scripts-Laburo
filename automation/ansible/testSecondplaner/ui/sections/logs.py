"""
Sección Logs / Reportes
"""
import questionary
from pathlib import Path
from typing import TYPE_CHECKING
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

if TYPE_CHECKING:
    from core.context import AppContext
    from core.engine import BackgroundEngine


class LogsSection:
    """Sección Logs y Reportes"""
    
    def __init__(self, context: "AppContext", engine: "BackgroundEngine"):
        self.context = context
        self.engine = engine
        self.console = Console()
    
    def run(self) -> None:
        """Ejecutar menú Logs"""
        while True:
            self.console.clear()
            self._show_header()
            
            action = questionary.select(
                "📋 Logs / Reportes",
                choices=[
                    "Ver Últimas Ejecuciones",
                    "Filtrar por Módulo",
                    "Exportar JSON",
                    "Exportar CSV",
                    "Abrir Carpeta Logs",
                    "⬅️ Volver"
                ]
            ).ask()
            
            if not action or action == "⬅️ Volver":
                break
            
            if action == "Ver Últimas Ejecuciones":
                self._show_recent_jobs()
            elif action == "Filtrar por Módulo":
                self._filter_by_module()
            elif action == "Exportar JSON":
                self._export_json()
            elif action == "Exportar CSV":
                self._export_csv()
            elif action == "Abrir Carpeta Logs":
                self._open_logs_folder()
            
            if action != "Abrir Carpeta Logs":
                input("\nPresiona Enter para continuar...")
    
    def _show_header(self) -> None:
        """Mostrar header de la sección"""
        self.console.print("[bold cyan]📋 Logs / Reportes[/bold cyan]")
        self.console.print("[dim]Historial de ejecuciones y reportes[/dim]\n")
    
    def _show_recent_jobs(self) -> None:
        """Mostrar trabajos recientes"""
        jobs = self.engine.get_all_jobs()
        
        if not jobs:
            self.console.print("[yellow]No hay ejecuciones recientes[/yellow]")
            return
        
        # Ordenar por tiempo (más reciente primero)
        jobs_sorted = sorted(jobs, key=lambda x: x.get("start_time", ""), reverse=True)[:20]
        
        table = Table(title="Últimas Ejecuciones")
        table.add_column("ID", style="cyan", width=10)
        table.add_column("Playbook", style="white")
        table.add_column("Target", style="magenta")
        table.add_column("Estado", justify="center")
        table.add_column("Hora", justify="right")
        
        for job in jobs_sorted:
            status_style = {
                "RUNNING": "yellow",
                "SUCCESS": "green",
                "FAILED": "red",
                "CANCELLED": "bright_black"
            }.get(job["status"], "white")
            
            table.add_row(
                job["id"],
                job["playbook"],
                job["target"],
                f"[{status_style}]{job['status']}[/{status_style}]",
                job.get("start_time", "-")
            )
        
        self.console.print(table)
    
    def _filter_by_module(self) -> None:
        """Filtrar por módulo"""
        modules = ["AD", "SCCM", "Hardware", "Network", "Software", "WLC", "Monitoring"]
        selected_module = questionary.select("Selecciona módulo:", choices=modules + ["⬅️ Volver"]).ask()
        
        if selected_module and selected_module != "⬅️ Volver":
            # Filtrar jobs por módulo (buscando en nombre del playbook)
            jobs = self.engine.get_all_jobs()
            filtered = [j for j in jobs if selected_module.lower() in j["playbook"].lower()]
            
            if filtered:
                self.console.print(f"[cyan]Jobs de {selected_module}:[/cyan]")
                for job in filtered[:10]:
                    self.console.print(f"  {job['id']}: {job['playbook']} - {job['status']}")
            else:
                self.console.print(f"[yellow]No hay jobs de {selected_module}[/yellow]")
    
    def _export_json(self) -> None:
        """Exportar jobs a JSON"""
        import json
        jobs = self.engine.get_all_jobs()
        
        if not jobs:
            self.console.print("[yellow]No hay jobs para exportar[/yellow]")
            return
        
        output_file = Path("logs") / f"jobs_export_{Path(__file__).parent.parent.parent.parent.name}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        
        self.console.print(f"[green]✓ Exportado a {output_file}[/green]")
    
    def _export_csv(self) -> None:
        """Exportar jobs a CSV"""
        import csv
        jobs = self.engine.get_all_jobs()
        
        if not jobs:
            self.console.print("[yellow]No hay jobs para exportar[/yellow]")
            return
        
        output_file = Path("logs") / f"jobs_export_{Path(__file__).parent.parent.parent.parent.name}.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "playbook", "target", "status", "start_time", "duration"])
            writer.writeheader()
            writer.writerows(jobs)
        
        self.console.print(f"[green]✓ Exportado a {output_file}[/green]")
    
    def _open_logs_folder(self) -> None:
        """Abrir carpeta de logs"""
        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        import os
        import platform
        
        if platform.system() == "Windows":
            os.startfile(logs_dir)
        elif platform.system() == "Darwin":
            os.system(f"open {logs_dir}")
        else:
            os.system(f"xdg-open {logs_dir}")
        
        self.console.print(f"[green]✓ Carpeta de logs abierta[/green]")
