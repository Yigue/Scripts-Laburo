# -*- coding: utf-8 -*-
"""
presentation/display/admin_formatters.py
========================================
Formateadores de resultados administrativos.

Contiene funciones para mostrar resultados de administración: LAPS, BitLocker keys,
AD info y audit groups.
"""

from rich.panel import Panel
from rich.table import Table
from rich import box

from ...shared.config import console, logger
from ...domain.models import ExecutionResult
from .general_formatters import mostrar_resultado, mostrar_dashboard_ejecucion


def mostrar_laps_resultado(result: ExecutionResult, hostname: str):
    """
    Muestra el resultado de LAPS de forma destacada.
    
    Args:
        result: Resultado de la ejecución del playbook de LAPS
        hostname: Nombre del host
    """
    if not result.success:
        mostrar_resultado(result, f"LAPS - {hostname}")
        return
    
    password = None
    expiration = None
    
    if result.data:
        try:
            plays = result.data.get("plays", [])
            for play in plays:
                tasks = play.get("tasks", [])
                for task in tasks:
                    hosts = task.get("hosts", {})
                    for host, host_result in hosts.items():
                        if "msg" in host_result:
                            msg = host_result["msg"]
                            if isinstance(msg, list):
                                for line in msg:
                                    if "Password:" in str(line):
                                        password = line.split("Password:")[-1].strip()
                                    elif "Expira:" in str(line):
                                        expiration = line.split("Expira:")[-1].strip()
        except Exception:
            pass
    
    if password:
        console.print(Panel(
            f"[green bold]🔑 Password LAPS[/green bold]\n\n"
            f"[white bold]{password}[/white bold]\n\n"
            f"[dim]Expira: {expiration or 'N/A'}[/dim]",
            title=f"LAPS - {hostname}",
            border_style="green"
        ))
    else:
        mostrar_resultado(result, f"LAPS - {hostname}")


def mostrar_bitlocker_resultado(result: ExecutionResult, hostname: str):
    """
    Muestra las claves de BitLocker de forma destacada.
    
    Args:
        result: Resultado de la ejecución del playbook de BitLocker
        hostname: Nombre del host
    """
    if not result.success:
        mostrar_resultado(result, f"BitLocker Recovery - {hostname}")
        return
    
    keys = []
    
    if result.data:
        try:
            plays = result.data.get("plays", [])
            for play in plays:
                tasks = play.get("tasks", [])
                for task in tasks:
                    hosts = task.get("hosts", {})
                    for host, host_result in hosts.items():
                        if "msg" in host_result:
                            msg = host_result["msg"]
                            if isinstance(msg, list):
                                for line in msg:
                                    if "Recovery Password:" in str(line):
                                        keys.append(line.split("Recovery Password:")[-1].strip())
        except Exception:
            pass
    
    if keys:
        content = "[green bold]🔐 Claves de Recuperación BitLocker[/green bold]\n\n"
        for i, key in enumerate(keys, 1):
            content += f"[white bold]Clave {i}:[/white bold] {key}\n"
        content += "\n[dim]Guardar estas claves en un lugar seguro[/dim]"
        
        console.print(Panel(
            content,
            title=f"BitLocker - {hostname}",
            border_style="green"
        ))
    else:
        mostrar_resultado(result, f"BitLocker Recovery - {hostname}")


def mostrar_ad_info(result: ExecutionResult, hostname: str):
    """Muestra información de AD del equipo."""
    if not result.data:
        mostrar_resultado(result, f"Info AD - {hostname}")
        return

    try:
        # Nota: Este playbook usa hosts: localhost, así que los datos están en 'localhost'
        res = result.data["plays"][0]["tasks"][0]["hosts"]["localhost"]
        info = res.get("msg", {})
        
        if "error" in info:
            console.print(f"[red]❌ Error de AD: {info['error']}[/red]")
            return

        table = Table(title=f"🏢 Información Active Directory - {hostname}", box=box.ROUNDED)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="white")
        
        table.add_row("Nombre AD", info.get("name", "N/A"))
        table.add_row("OS", info.get("os", "N/A"))
        table.add_row("Versión OS", info.get("os_version", "N/A"))
        table.add_row("Creado", info.get("created", "N/A"))
        table.add_row("Último Login", info.get("last_logon", "N/A"))
        table.add_row("IP en AD", info.get("ip", "N/A"))
        table.add_row("DN", info.get("dn", "N/A"), style="dim")
        
        console.print(table)
    except Exception as e:
        logger.error(f"Error parseando AD info: {e}")
        mostrar_resultado(result, f"Info AD - {hostname}")


def mostrar_audit_groups_resultado(result: ExecutionResult, hostname: str):
    """Muestra auditoría de grupos de AD."""
    if not result.data:
        mostrar_resultado(result, f"Auditoría de Grupos - {hostname}")
        return

    try:
        res = result.data["plays"][0]["tasks"][0]["hosts"]["localhost"]
        info = res.get("msg", {})
        
        if "error" in info:
            console.print(f"[red]❌ Error: {info['error']}[/red]")
            return

        console.print(f"\n[bold cyan]👥 Grupos de AD para {hostname}:[/bold cyan]")
        groups = info.get("computer_groups", [])
        if groups:
            for group in sorted(groups):
                console.print(f"  • {group}")
        else:
            console.print("  [yellow]No se encontraron grupos o acceso denegado[/yellow]")
        
        mostrar_dashboard_ejecucion(result, f"Auditoría de Grupos - {hostname}")
    except Exception as e:
        logger.error(f"Error parseando audit groups: {e}")
        mostrar_resultado(result, f"Auditoría de Grupos - {hostname}")
