"""
Sección Targets - Gestión de targets activos
"""
import os
from pathlib import Path
from typing import TYPE_CHECKING
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

if TYPE_CHECKING:
    from core.context import AppContext


class TargetsSection:
    """Sección para gestionar targets"""
    
    def __init__(self, context: "AppContext"):
        self.context = context
        self.console = Console()
    
    def run(self) -> None:
        """Ejecutar menú de targets"""
        while True:
            self.console.clear()
            self._show_status()
            
            action = questionary.select(
                "🎯 Gestión de Targets",
                choices=[
                    "Set Target (hostname/IP)",
                    "Set Bulk Targets (pegar lista)",
                    "Import Targets (desde archivo)",
                    "Clear Target",
                    "Show Target Details",
                    "List Active Targets",
                    "⬅️ Volver"
                ]
            ).ask()
            
            if not action or action == "⬅️ Volver":
                break
            
            if action == "Set Target (hostname/IP)":
                self._set_target()
            elif action == "Set Bulk Targets (pegar lista)":
                self._set_bulk_targets()
            elif action == "Import Targets (desde archivo)":
                self._import_targets()
            elif action == "Clear Target":
                self._clear_target()
            elif action == "Show Target Details":
                self._show_target_details()
            elif action == "List Active Targets":
                self._list_targets()
            
            if action != "List Active Targets":
                input("\nPresiona Enter para continuar...")
    
    def _show_status(self) -> None:
        """Mostrar estado actual de targets"""
        status_table = Table(title="Estado de Targets", show_header=False)
        status_table.add_column("Propiedad", style="cyan")
        status_table.add_column("Valor", style="white")
        
        status_table.add_row("Target Activo", self.context.target or "[dim]No seteado[/dim]")
        status_table.add_row("Targets Bulk", str(len(self.context.targets)) if self.context.targets else "[dim]Ninguno[/dim]")
        
        self.console.print(Panel(status_table, border_style="blue"))
    
    def _set_target(self) -> None:
        """Establecer target activo"""
        target = questionary.text("Ingresa el hostname/IP del target:").ask()
        if target:
            self.context.set_target(target)
            self.console.print(f"[green]✓ Target establecido: {target.upper()}[/green]")
    
    def _set_bulk_targets(self) -> None:
        """Establecer múltiples targets"""
        self.console.print("[yellow]Pega la lista de targets (uno por línea, separados por comas o espacios):[/yellow]")
        targets_text = questionary.text("Targets:").ask()
        
        if targets_text:
            # Dividir por líneas, comas o espacios
            targets = []
            for line in targets_text.split("\n"):
                for item in line.replace(",", " ").split():
                    if item.strip():
                        targets.append(item.strip())
            
            if targets:
                self.context.add_targets(targets)
                self.console.print(f"[green]✓ {len(targets)} targets agregados[/green]")
    
    def _import_targets(self) -> None:
        """Importar targets desde archivo"""
        file_path = questionary.path("Ruta al archivo (CSV/TXT):").ask()
        
        if file_path and Path(file_path).exists():
            try:
                targets = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        # Dividir por comas si es CSV, sino por espacios
                        if "," in line:
                            items = line.strip().split(",")
                        else:
                            items = line.strip().split()
                        
                        for item in items:
                            if item.strip():
                                targets.append(item.strip())
                
                if targets:
                    self.context.add_targets(targets)
                    self.console.print(f"[green]✓ {len(targets)} targets importados desde {file_path}[/green]")
            except Exception as e:
                self.console.print(f"[red]Error al importar: {e}[/red]")
    
    def _clear_target(self) -> None:
        """Limpiar target activo"""
        if self.context.target:
            if questionary.confirm(f"¿Limpiar target activo ({self.context.target})?").ask():
                self.context.set_target("")
                self.console.print("[green]✓ Target limpiado[/green]")
        else:
            self.console.print("[yellow]No hay target activo para limpiar[/yellow]")
    
    def _show_target_details(self) -> None:
        """Mostrar detalles del target"""
        if not self.context.target:
            self.console.print("[yellow]No hay target activo[/yellow]")
            return
        
        self.console.print(f"[cyan]Verificando conexión a {self.context.target}...[/cyan]")
        # Aquí podrías implementar ping/WinRM check real
        self.console.print("[dim]Funcionalidad de verificación pendiente de implementar[/dim]")
    
    def _list_targets(self) -> None:
        """Listar todos los targets"""
        if not self.context.target and not self.context.targets:
            self.console.print("[yellow]No hay targets configurados[/yellow]")
            return
        
        table = Table(title="Targets Activos")
        table.add_column("Tipo", style="cyan")
        table.add_column("Target", style="white")
        
        if self.context.target:
            table.add_row("Activo", f"[bold]{self.context.target}[/bold]")
        
        for i, target in enumerate(self.context.targets, 1):
            table.add_row("Bulk", target)
        
        self.console.print(table)
