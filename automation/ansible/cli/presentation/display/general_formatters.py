# -*- coding: utf-8 -*-
"""
presentation/display/general_formatters.py
==========================================
Formateadores generales de resultados.

Contiene funciones para mostrar resultados genéricos, historial, dashboard y snapshots de hosts.
"""

from datetime import datetime
from typing import List

from rich.panel import Panel

from ...shared.config import BASE_DIR, console, logger
from ...domain.models import ExecutionResult, HostSnapshot


def mostrar_host_snapshot(snapshot: HostSnapshot):
    """
    Muestra un resumen rápido del host arriba del menú.
    """
    content = (
        f"[cyan]Usuario:[/cyan] [bold white]{snapshot.user}[/bold white] | "
        f"[cyan]OS:[/cyan] [bold white]{snapshot.os}[/bold white]\n"
        f"[cyan]Disco C:[/cyan] [bold white]{snapshot.disk_free} GB libres[/bold white] "
        f"[dim](de {snapshot.disk_total} GB)[/dim]"
    )
    
    console.print(Panel(
        content,
        title=f"📍 {snapshot.hostname}",
        border_style="blue",
        title_align="left"
    ))


def mostrar_resultado(result: ExecutionResult, titulo: str = "Resultado"):
    """
    Muestra el resultado de una ejecución de forma formateada.
    
    Args:
        result: Resultado de la ejecución
        titulo: Título del panel
    """
    if result.success:
        console.print(Panel(
            f"[green]✅ Operación completada exitosamente[/green]",
            title=titulo,
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]❌ La operación falló[/red]",
            title=titulo,
            border_style="red"
        ))
    
    # Si hay datos JSON, intentar mostrarlos
    if result.data:
        try:
            plays = result.data.get("plays", [])
            has_tasks = False
            for play in plays:
                tasks = play.get("tasks", [])
                for task in tasks:
                    has_tasks = True
                    task_name = task.get("task", {}).get("name", "")
                    hosts = task.get("hosts", {})
                    for host, host_result in hosts.items():
                        # Mostrar mensajes de debug
                        if "msg" in host_result:
                            msg = host_result["msg"]
                            if isinstance(msg, list):
                                console.print(f"\n[cyan]{task_name}:[/cyan]")
                                for line in msg:
                                    console.print(f"  {line}")
                            else:
                                console.print(f"\n[cyan]{task_name}:[/cyan] {msg}")
                        # Mostrar errores
                        if "failed" in host_result and host_result["failed"]:
                            console.print(f"[red]Error en {host}: {host_result.get('msg', 'Sin detalles')}[/red]")
            
            if not has_tasks:
                # Si no hay tareas, mostrar mensaje
                console.print("[dim]No hay información adicional disponible[/dim]")
        except Exception as e:
            logger.error(f"Error mostrando datos: {e}")
    
    # Mostrar stderr si existe
    if result.stderr:
        console.print(f"\n[red dim]Error: {result.stderr[:500]}[/red dim]")
    
    # Mostrar duración
    if result.duration:
        console.print(f"\n[dim]⏱️ Duración: {result.duration:.2f}s[/dim]")


def mostrar_dashboard_ejecucion(result: ExecutionResult, tarea: str):
    """
    Muestra un resumen rápido de la ejecución (estado y duración).
    """
    estado = "[green]✅ Exitoso[/green]" if result.success else "[red]❌ Fallido[/red]"
    duracion = f"{result.duration:.2f}s"
    
    from rich.columns import Columns
    console.print(f"\n[dim]📊 {tarea}: {estado} en {duracion}[/dim]\n")


def mostrar_historial_sesion(entries: List):
    """Muestra el historial completo de la sesión en una tabla."""
    if not entries:
        console.print("\n[yellow]No hay tareas registradas en esta sesión.[/yellow]\n")
        return

    from rich.table import Table
    from rich import box
    
    table = Table(title="📜 Historial de Ejecuciones (Sesión Actual)", box=box.ROUNDED, show_lines=True)
    table.add_column("Hora", style="dim")
    table.add_column("Host", style="cyan")
    table.add_column("Tarea", style="white")
    table.add_column("Estado", justify="center")
    table.add_column("Duración", justify="right", style="magenta")

    for entry in entries:
        estado = "[green]OK[/green]" if entry.success else "[red]Error[/red]"
        table.add_row(
            entry.timestamp,
            entry.hostname,
            entry.task_name,
            estado,
            f"{entry.duration:.2f}s"
        )

    console.print("\n")
    console.print(table)
    console.print("\n")


def guardar_reporte(hostname: str):
    """Guarda el contenido actual de la consola en un archivo HTML."""
    (BASE_DIR / "reports").mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reporte_{hostname}_{timestamp}.html"
    filepath = BASE_DIR / "reports" / filename
    
    try:
        console.save_html(str(filepath))
        console.print(f"\n[green]📁 Reporte guardado en: [bold]{filepath}[/bold][/green]")
        return str(filepath)
    except Exception as e:
        logger.error(f"Error guardando reporte: {e}")
        console.print(f"\n[red]❌ No se pudo guardar el reporte: {e}[/red]")
        return None
