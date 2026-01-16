# -*- coding: utf-8 -*-
"""
cli/task_panel.py
=================
Panel lateral de seguimiento de tareas en tiempo real.
"""

from typing import List, Optional
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich import box
from rich.align import Align

from .config import console
from .task_manager import task_manager, TaskStatus


def render_task_panel(tasks: List[TaskStatus]) -> Panel:
    """
    Renderiza el panel lateral con las tareas activas.
    
    Args:
        tasks: Lista de tareas a mostrar
        
    Returns:
        Panel: Panel de Rich con la información de tareas
    """
    if not tasks:
        return Panel(
            Align.center("[dim]No hay tareas activas[/dim]", vertical="middle"),
            title="[cyan]Tareas Activas[/cyan]",
            border_style="cyan",
            box=box.ROUNDED,
            width=35
        )
    
    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=box.SIMPLE,
        border_style="cyan",
        width=33
    )
    table.add_column("Estado", width=8, justify="center")
    table.add_column("Tarea", width=15, no_wrap=True)
    table.add_column("Target", width=10, no_wrap=True)
    
    for task in tasks:
        # Determinar icono y color según estado
        if task.status == "RUNNING":
            status_icon = "[yellow]●[/yellow]"
        elif task.status == "SUCCESS":
            status_icon = "[green]✓[/green]"
        elif task.status == "FAILED":
            status_icon = "[red]✗[/red]"
        else:
            status_icon = "[dim]—[/dim]"
        
        # Truncar nombres largos
        task_name = task.task_name[:13] + "..." if len(task.task_name) > 13 else task.task_name
        target = task.target[:8] + "..." if len(task.target) > 8 else task.target
        
        table.add_row(
            status_icon,
            f"[dim]{task_name}[/dim]",
            f"[dim]{target}[/dim]"
        )
    
    summary = task_manager.get_summary()
    summary_text = (
        f"[green]✓ {summary['SUCCESS']}[/green] | "
        f"[yellow]● {summary['RUNNING']}[/yellow] | "
        f"[red]✗ {summary['FAILED']}[/red]"
    )
    
    content = table
    content = f"{content}\n\n{summary_text}"
    
    return Panel(
        content,
        title="[cyan]Tareas Activas[/cyan]",
        border_style="cyan",
        box=box.ROUNDED,
        width=35
    )


def show_task_panel_live(duration: Optional[float] = None) -> None:
    """
    Muestra el panel de tareas con actualización en tiempo real.
    
    Args:
        duration: Duración en segundos para mostrar (None = hasta interrupción)
    """
    import time as time_module
    
    start_time = time_module.time()
    
    def get_renderable():
        active_tasks = task_manager.get_active_tasks()
        return render_task_panel(active_tasks)
    
    with Live(get_renderable(), refresh_per_second=2, console=console) as live:
        while True:
            if duration and (time_module.time() - start_time) >= duration:
                break
            
            active_tasks = task_manager.get_active_tasks()
            if not active_tasks and duration:
                # Si no hay tareas y hay duración, esperar un poco antes de salir
                time_module.sleep(0.5)
                continue
            
            live.update(get_renderable())
            time_module.sleep(0.5)


def get_task_panel() -> Panel:
    """
    Obtiene el panel de tareas sin Live (para usar en Layout).
    
    Returns:
        Panel: Panel de tareas actualizado
    """
    all_tasks = task_manager.get_all_tasks()
    # Mostrar solo las últimas 10 tareas (activas primero)
    active_tasks = task_manager.get_active_tasks()
    completed_tasks = [t for t in all_tasks if t.status != "RUNNING"]
    
    # Ordenar: activas primero, luego completadas por tiempo (más recientes primero)
    display_tasks = sorted(
        active_tasks + completed_tasks[-5:],  # Mostrar 5 completadas recientes
        key=lambda t: (t.status != "RUNNING", -(t.start_time.timestamp() if t.start_time else 0))
    )
    
    return render_task_panel(display_tasks[:10])  # Máximo 10 tareas
