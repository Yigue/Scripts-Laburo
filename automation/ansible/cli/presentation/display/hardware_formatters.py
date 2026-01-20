# -*- coding: utf-8 -*-
"""
presentation/display/hardware_formatters.py
===========================================
Formateadores de resultados de hardware.

Contiene funciones para mostrar resultados de hardware: specs, updates, bitlocker status,
auditoría de salud, métricas y health checks.
"""

import json
from rich.table import Table
from rich import box

from ...shared.config import console, logger
from ...domain.models import ExecutionResult
from .general_formatters import mostrar_resultado, mostrar_dashboard_ejecucion


def mostrar_specs_tabla(result: ExecutionResult, hostname: str):
    """
    Muestra las especificaciones del sistema en una tabla Rich.
    
    Args:
        result: Resultado de la ejecución del playbook de specs
        hostname: Nombre del host para el título
    """
    if not result.data:
        mostrar_resultado(result, f"Especificaciones - {hostname}")
        return
    
    table = Table(
        title=f"💻 Especificaciones - {hostname}",
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED
    )
    table.add_column("Propiedad", style="cyan", width=25)
    table.add_column("Valor", style="green")
    
    rows_added = 0
    
    try:
        plays = result.data.get("plays", [])
        for play in plays:
            tasks = play.get("tasks", [])
            for task in tasks:
                hosts = task.get("hosts", {})
                for host, host_result in hosts.items():
                    # Buscar ansible_facts con system_specs
                    if "ansible_facts" in host_result:
                        facts = host_result["ansible_facts"]
                        if "system_specs" in facts:
                            specs = facts["system_specs"]
                            for key, value in specs.items():
                                if value and str(value) != "N/A":
                                    prop = key.replace("_", " ").title()
                                    table.add_row(prop, str(value))
                                    rows_added += 1
                    # Fallback a stdout_lines
                    elif "stdout_lines" in host_result:
                        for line in host_result["stdout_lines"]:
                            if ":" in line and "===" not in line:
                                parts = line.split(":", 1)
                                if len(parts) == 2:
                                    prop = parts[0].strip()
                                    val = parts[1].strip()
                                    if prop and val:
                                        table.add_row(prop, val)
                                        rows_added += 1
                    # Fallback: msg (algunos debug usan msg)
                    elif "msg" in host_result:
                        msg = host_result["msg"]
                        lines = msg if isinstance(msg, list) else str(msg).splitlines()
                        for line in lines:
                            if ":" in line and "===" not in line:
                                parts = line.split(":", 1)
                                if len(parts) == 2:
                                    prop = parts[0].strip()
                                    val = parts[1].strip()
                                    if prop and val:
                                        table.add_row(prop, val)
                                        rows_added += 1
    except Exception as e:
        console.print(f"[yellow]Error parseando datos: {e}[/yellow]")
        mostrar_resultado(result, f"Especificaciones - {hostname}")
        return
    
    if rows_added > 0:
        console.print(table)
    else:
        mostrar_resultado(result, f"Especificaciones - {hostname}")


def mostrar_updates_resultado(result: ExecutionResult, hostname: str):
    """Muestra actualizaciones de Windows pendientes."""
    if not result.data:
        mostrar_resultado(result, f"Windows Updates - {hostname}")
        return

    table = Table(title=f"🔄 Updates Pendientes - {hostname}", box=box.ROUNDED)
    table.add_column("KB", style="cyan")
    table.add_column("Título", style="white")
    table.add_column("Severidad", style="red")

    try:
        res = result.data["plays"][0]["tasks"][0]["hosts"][hostname]
        updates_data = res.get("windows_updates", {})
        pending = updates_data.get("updates", [])
        
        if not pending:
            console.print(f"[green]✅ No hay actualizaciones pendientes en {hostname}[/green]")
            return

        for up in pending:
            table.add_row(up.get("kb", "N/A"), up.get("title", "N/A")[:60], up.get("severity", "N/A"))
        
        console.print(table)
        console.print(f"\n[yellow]Total: {len(pending)} actualizaciones pendientes[/yellow]")
    except Exception as e:
        logger.error(f"Error parseando updates: {e}")
        mostrar_resultado(result, f"Windows Updates - {hostname}")


def mostrar_bitlocker_status_tabla(result: ExecutionResult, hostname: str):
    """Muestra estado detallado de BitLocker."""
    if not result.data:
        mostrar_resultado(result, f"Estado BitLocker - {hostname}")
        return

    try:
        res = result.data["plays"][0]["tasks"][0]["hosts"][hostname]
        status = res.get("bitlocker_status", {})
        
        table = Table(title=f"🔐 Estado BitLocker - {hostname}", box=box.ROUNDED)
        table.add_column("Propiedad", style="cyan")
        table.add_column("Valor", style="green")
        
        table.add_row("Protección", "ENCENDIDA" if status.get("enabled") else "APAGADA")
        table.add_row("Porcentaje", f"{status.get('encryption_percentage')}%")
        table.add_row("Estado", status.get("volume_status", "N/A"))
        table.add_row("Protectores", status.get("key_protector", "N/A"))
        
        console.print(table)
    except Exception as e:
        logger.error(f"Error parseando bitlocker status: {e}")
        mostrar_resultado(result, f"Estado BitLocker - {hostname}")


def mostrar_auditoria_salud(result: ExecutionResult, hostname: str):
    """Muestra el resultado del combo de Auditoría de Salud."""
    if not result.data:
        mostrar_resultado(result, f"Auditoría de Salud - {hostname}")
        return

    try:
        plays = result.data.get("plays", [])
        if not plays:
            mostrar_resultado(result, f"Auditoría de Salud - {hostname}")
            return
            
        # Buscar la tarea 'Resumen de Auditoría'
        data = {}
        for task in plays[0].get("tasks", []):
            if task.get("task", {}).get("name") == "Resumen de Auditoría":
                data = task.get("hosts", {}).get(hostname, {}).get("msg", {})
                break
        
        if not data:
            mostrar_resultado(result, f"Auditoría de Salud - {hostname}")
            return

        console.print(f"\n[bold magenta]🏥 Reporte de Auditoría de Salud: {hostname}[/bold magenta]\n")
        
        # 1. Specs summary
        console.print("[bold cyan]1. Especificaciones:[/bold cyan]")
        specs_data = data.get("specs", {})
        try:
            specs = specs_data.get("ansible_facts", {}).get("system_specs", {})
            if specs:
                console.print(f"   CPU: {specs.get('processor', 'N/A')} | RAM: {specs.get('memory_ram', 'N/A')}")
            else:
                console.print("   [dim]Parcialmente disponible[/dim]")
        except:
            console.print("   [dim]No disponible[/dim]")
            
        # 2. Battery
        console.print("\n[bold cyan]2. Estado de Batería:[/bold cyan]")
        battery = data.get("battery", {})
        if battery.get("failed") or "No se pudo" in str(battery):
            console.print("   [yellow]No posee batería o error en lectura[/yellow]")
        else:
            console.print("   [green]Lectura completada exitosamente[/green]")

        # 3. SMART
        console.print("\n[bold cyan]3. Salud de Disco (SMART):[/bold cyan]")
        smart_data = data.get("smart", {})
        smart_lines = smart_data.get("stdout_lines", [])
        if smart_lines:
            status = "OK" if any("OK" in line for line in smart_lines) else "Verificar"
            console.print(f"   Estado SMART: [bold green]{status}[/bold green]")
        else:
            console.print("   [dim]No disponible[/dim]")

        # 4. Updates
        console.print("\n[bold cyan]4. Updates Pendientes:[/bold cyan]")
        updates_data = data.get("updates", {})
        win_updates = updates_data.get("windows_updates", {})
        count = len(win_updates.get("updates", []))
        color = "red" if count > 0 else "green"
        console.print(f"   Actualizaciones pendientes: [bold {color}]{count}[/bold {color}]")
        
        mostrar_dashboard_ejecucion(result, f"Auditoría de Salud - {hostname}")
        
    except Exception as e:
        logger.error(f"Error parseando health audit: {e}")
        mostrar_resultado(result, f"Auditoría de Salud - {hostname}")


