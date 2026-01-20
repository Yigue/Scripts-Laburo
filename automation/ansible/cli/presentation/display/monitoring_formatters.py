# -*- coding: utf-8 -*-
"""
presentation/display/monitoring_formatters.py
==============================================
Formateadores de resultados de monitoreo.

Contiene funciones para mostrar resultados de monitoreo: métricas y health checks.
"""

import json
from rich.table import Table
from rich import box

from ...shared.config import console, logger
from ...domain.models import ExecutionResult
from .general_formatters import mostrar_resultado, mostrar_dashboard_ejecucion


def mostrar_metricas_resultado(result: ExecutionResult, hostname: str):
    """Muestra las métricas del sistema recopiladas (M1)."""
    if not result.data:
        mostrar_resultado(result, f"Métricas - {hostname}")
        return

    try:
        plays = result.data.get("plays", [])
        if not plays:
            mostrar_resultado(result, f"Métricas - {hostname}")
            return
        
        # Buscar la tarea que tiene system_metrics
        metrics_data = None
        for play in plays:
            tasks = play.get("tasks", [])
            for task in tasks:
                hosts = task.get("hosts", {})
                host_result = hosts.get(hostname, {})
                
                # Buscar en ansible_facts (tarea "Parsear métricas")
                if "ansible_facts" in host_result:
                    facts = host_result["ansible_facts"]
                    if "system_metrics" in facts:
                        metrics_data = facts["system_metrics"]
                        break
                
                # Buscar en stdout de la tarea "Recolectar métricas clave" (parsear JSON)
                task_name = task.get("task", {}).get("name", "")
                if "Recolectar métricas" in task_name and "stdout" in host_result:
                    try:
                        stdout = host_result["stdout"].strip()
                        if stdout and stdout.startswith("{"):
                            metrics_data = json.loads(stdout)
                            break
                    except:
                        pass
        
        # Si no encontramos en estructura, buscar en msg del debug
        if not metrics_data:
            for play in plays:
                tasks = play.get("tasks", [])
                for task in tasks:
                    if task.get("task", {}).get("name") == "Mostrar métricas actuales":
                        hosts = task.get("hosts", {})
                        host_result = hosts.get(hostname, {})
                        if "msg" in host_result:
                            msg = host_result["msg"]
                            if isinstance(msg, list):
                                metrics_data = {}
                                for line in msg:
                                    if "CPU Load:" in line:
                                        try:
                                            metrics_data["CPU_Load"] = float(line.split(":")[1].replace("%", "").strip())
                                        except:
                                            pass
                                    elif "Memory usage:" in line:
                                        try:
                                            metrics_data["Mem_Used_Percent"] = float(line.split(":")[1].replace("%", "").strip())
                                        except:
                                            pass
                                    elif "Time:" in line:
                                        try:
                                            metrics_data["Timestamp"] = line.split("Time:")[1].strip()
                                        except:
                                            pass
        
        if not metrics_data:
            mostrar_resultado(result, f"Métricas - {hostname}")
            return
        
        # Crear tabla formateada
        table = Table(
            title=f"📊 Métricas del Sistema - {hostname}",
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED
        )
        table.add_column("Métrica", style="cyan", width=25)
        table.add_column("Valor", style="green", justify="right")
        
        # CPU Load con indicador de color
        cpu_load = metrics_data.get("CPU_Load", 0)
        cpu_color = "green" if cpu_load < 50 else "yellow" if cpu_load < 80 else "red"
        table.add_row("CPU Load", f"[{cpu_color}]{cpu_load}%[/{cpu_color}]")
        
        # Memory usage con indicador de color
        mem_percent = metrics_data.get("Mem_Used_Percent", 0)
        mem_color = "green" if mem_percent < 70 else "yellow" if mem_percent < 90 else "red"
        table.add_row("Memoria Usada", f"[{mem_color}]{mem_percent}%[/{mem_color}]")
        
        # Timestamp
        timestamp = metrics_data.get("Timestamp", "N/A")
        table.add_row("Timestamp", timestamp)
        
        # Mostrar error si existe
        if "Error" in metrics_data:
            table.add_row("[red]Error[/red]", f"[red]{metrics_data['Error']}[/red]")
        
        console.print("\n")
        console.print(table)
        console.print("\n")
        
        mostrar_dashboard_ejecucion(result, f"Métricas - {hostname}")
        
    except Exception as e:
        logger.error(f"Error parseando métricas: {e}")
        mostrar_resultado(result, f"Métricas - {hostname}")


def mostrar_health_resultado(result: ExecutionResult, hostname: str):
    """Muestra los health checks del sistema (M2)."""
    if not result.data:
        mostrar_resultado(result, f"Health Checks - {hostname}")
        return

    try:
        plays = result.data.get("plays", [])
        if not plays:
            mostrar_resultado(result, f"Health Checks - {hostname}")
            return
        
        # Buscar la tarea que tiene system_health
        health_data = None
        for play in plays:
            tasks = play.get("tasks", [])
            for task in tasks:
                hosts = task.get("hosts", {})
                host_result = hosts.get(hostname, {})
                
                # Buscar en ansible_facts (tarea "Parsear resultados de salud")
                if "ansible_facts" in host_result:
                    facts = host_result["ansible_facts"]
                    if "system_health" in facts:
                        health_data = facts["system_health"]
                        break
                
                # Buscar en stdout de la tarea "Ejecutar Health Checks" (parsear JSON)
                task_name = task.get("task", {}).get("name", "")
                if "Health Checks" in task_name and "stdout" in host_result:
                    try:
                        stdout = host_result["stdout"].strip()
                        if stdout and stdout.startswith("{"):
                            health_data = json.loads(stdout)
                            break
                    except:
                        pass
        
        if not health_data:
            mostrar_resultado(result, f"Health Checks - {hostname}")
            return
        
        console.print(f"\n[bold magenta]🏥 Health Checks - {hostname}[/bold magenta]\n")
        
        # 1. Uptime
        uptime = health_data.get("Uptime", "N/A")
        console.print(f"[cyan]⏱️  Último Boot:[/cyan] [white]{uptime}[/white]")
        
        # 2. Disco
        disk = health_data.get("Disk", {})
        if disk:
            free_percent = disk.get("FreePercent", 0)
            status = disk.get("Status", "UNKNOWN")
            status_color = "green" if status == "OK" else "yellow" if status == "WARNING" else "red"
            
            console.print(f"\n[cyan]💾 Disco C::[/cyan]")
            console.print(f"  Espacio libre: [{status_color}]{free_percent}%[/{status_color}]")
            console.print(f"  Estado: [{status_color}]{status}[/{status_color}]")
        else:
            console.print(f"\n[cyan]💾 Disco C::[/cyan] [red]No disponible[/red]")
        
        # 3. Servicios
        services = health_data.get("Services", [])
        if services:
            console.print(f"\n[cyan]🔧 Servicios Críticos:[/cyan]")
            services_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
            services_table.add_column("Servicio", style="white")
            services_table.add_column("Estado", justify="center", width=15)
            
            all_ok = True
            for svc in services:
                svc_name = svc.get("Name", "N/A")
                svc_status = svc.get("Status", "UNKNOWN")
                
                if svc_status == "Running":
                    status_display = "[green]✓ Running[/green]"
                elif svc_status == "NOT_FOUND":
                    status_display = "[yellow]⚠ No encontrado[/yellow]"
                    all_ok = False
                elif svc_status == "Stopped":
                    status_display = "[red]✗ Stopped[/red]"
                    all_ok = False
                else:
                    status_display = f"[yellow]{svc_status}[/yellow]"
                    all_ok = False
                
                services_table.add_row(svc_name, status_display)
            
            console.print(services_table)
            
            if all_ok:
                console.print("\n[green]✅ Todos los servicios críticos están corriendo[/green]")
            else:
                console.print("\n[yellow]⚠️  Algunos servicios críticos no están en estado óptimo[/yellow]")
        else:
            console.print(f"\n[cyan]🔧 Servicios Críticos:[/cyan] [yellow]No hay servicios configurados[/yellow]")
        
        console.print("\n")
        
        mostrar_dashboard_ejecucion(result, f"Health Checks - {hostname}")
        
    except Exception as e:
        logger.error(f"Error parseando health checks: {e}")
        mostrar_resultado(result, f"Health Checks - {hostname}")
