# -*- coding: utf-8 -*-
"""
cli/display.py
==============
Funciones de visualización con Rich.

Contiene:
- clear_screen(): Limpia la pantalla
- show_banner(): Muestra el banner de la app
- show_menu_summary(): Muestra resumen de categorías
- mostrar_resultado(): Muestra resultado genérico
- mostrar_specs_tabla(): Muestra specs en tabla
- mostrar_laps_resultado(): Muestra resultado de LAPS
- mostrar_bitlocker_resultado(): Muestra claves de BitLocker
"""

import os

from rich.panel import Panel
from rich.table import Table
from rich import box

from .config import console, logger, BASE_DIR
from .models import ExecutionResult, HostSnapshot
from .menu_data import MENU_CATEGORIES


def clear_screen():
    """Limpia la pantalla del terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_banner():
    """Muestra el banner minimalista."""
    console.print("[cyan bold]IT-OPS CLI[/cyan bold] [dim]| Automatización IT con Ansible[/dim]\n")


def show_menu_summary():
    """Muestra un resumen minimalista de las categorías disponibles."""
    # Versión minimalista - solo mostrar en una línea simple si es necesario
    pass  # Se omite para diseño minimalista


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
                                    if line:
                                        console.print(f"  {line}")
                            else:
                                console.print(f"\n[cyan]{task_name}:[/cyan] {msg}")
                        # Mostrar stdout_lines
                        elif "stdout_lines" in host_result:
                            console.print(f"\n[cyan]{task_name}:[/cyan]")
                            for line in host_result["stdout_lines"]:
                                console.print(f"  {line}")
                        # Caso especial: fallido sin msg ni stdout_lines
                        elif host_result.get("failed", False):
                            console.print(f"\n[red]Tarea fallida: {task_name}[/red]")
                            if "module_stderr" in host_result:
                                console.print(f"  [dim]{host_result['module_stderr']}[/dim]")
            
            # Si no hubo tareas (ej: host no encontrado)
            if not has_tasks and result.stdout:
                console.print("\n[yellow]No se ejecutaron tareas. Salida de Ansible:[/yellow]")
                console.print(f"[dim]{result.stdout[:1000]}[/dim]")
                
        except Exception as e:
            logger.debug(f"Error parseando resultado JSON: {e}")
            if result.stdout:
                console.print("\n[dim]Raw output:[/dim]")
                console.print(result.stdout[:2000])
    elif result.stdout:
        # Si no hay data pero hay output
        console.print("\n[yellow]Salida del comando:[/yellow]")
        console.print(result.stdout[:2000])
    
    # Mostrar errores si hay
    if result.stderr and not result.success:
        console.print(f"\n[red]Errores:[/red]\n{result.stderr[:500]}")


def mostrar_dashboard_ejecucion(result: ExecutionResult, tarea: str):
    """Muestra un resumen compacto de la ejecución."""
    estado = "[bold green]ÉXITO[/bold green]" if result.success else "[bold red]FALLO[/bold red]"
    duracion = f"{result.duration:.2f}s"
    
    # Grid simple en lugar de tabla completa con bordes pesados
    from rich.columns import Columns
    console.print(f"\n[dim]📊 {tarea}: {estado} en {duracion}[/dim]\n")


def mostrar_historial_sesion(entries: list):
    """Muestra el historial completo de la sesión en una tabla."""
    if not entries:
        console.print("\n[yellow]No hay tareas registradas en esta sesión.[/yellow]\n")
        return

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


def mostrar_specs_tabla(result: ExecutionResult, hostname: str):
    """
    Muestra las especificaciones del sistema en una tabla Rich.
    
    Parsea el output de Ansible buscando datos en ansible_facts,
    stdout_lines, o msg y los presenta en una tabla formateada.
    
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
        # Si no se agregaron filas, mostrar resultado genérico
        mostrar_resultado(result, f"Especificaciones - {hostname}")


def mostrar_laps_resultado(result: ExecutionResult, hostname: str):
    """
    Muestra el resultado de LAPS de forma destacada.
    
    Busca el password y fecha de expiración en el output y los
    presenta en un panel formateado.
    
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
    
    Busca las claves de recuperación en el output y las presenta
    en un panel formateado.
    
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


def mostrar_auditoria_salud(result: ExecutionResult, hostname: str):
    """Muestra el resultado del combo de Auditoría de Salud."""
    if not result.data:
        mostrar_resultado(result, f"Auditoría de Salud - {hostname}")
        return

    try:
        # El resultado del combo está en la última tarea 'Resumen de Auditoría'
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
        # Extraer specs de la estructura anidada
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


def guardar_reporte(hostname: str):
    """Guarda el contenido actual de la consola en un archivo HTML."""
    from datetime import datetime
    (BASE_DIR / "reports").mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reporte_{hostname}_{timestamp}.html"
    filepath = BASE_DIR / "reports" / filename
    
    try:
        # Limpiar grabación del buffer antes de guardar si quisiéramos solo la última tarea
        # pero por ahora guardamos todo lo que hay en el buffer de la sesión actual
        console.save_html(str(filepath))
        console.print(f"\n[green]📁 Reporte guardado en: [bold]{filepath}[/bold][/green]")
        return str(filepath)
    except Exception as e:
        logger.error(f"Error guardando reporte: {e}")
        console.print(f"\n[red]❌ No se pudo guardar el reporte: {e}[/red]")
        return None
