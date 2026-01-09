#!/usr/bin/env python3
"""
IT-Ops CLI - Herramienta de Automatización con Ansible
======================================================
CLI interactiva para soporte técnico usando Ansible como motor de ejecución.

Características:
- Menú interactivo con Questionary
- UI moderna con Rich
- Ejecución de playbooks Ansible con JSON output
- Health check antes de mostrar menú
- Validación de seguridad para target_host
- Integración con Active Directory (LAPS, BitLocker, Unlock)
"""

import os
import sys
import json
import subprocess
import getpass
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from pathlib import Path

# Verificar dependencias
try:
    import questionary
    from questionary import Style
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.text import Text
    from rich.markdown import Markdown
    from rich import box
except ImportError as e:
    print(f"Error: Falta dependencia - {e}")
    print("Ejecutar: pip install -r requirements.txt")
    sys.exit(1)

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.absolute()
os.chdir(BASE_DIR)

# Consola Rich global
console = Console()

# Estilo personalizado para Questionary
CUSTOM_STYLE = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:white bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:cyan bold'),
    ('selected', 'fg:green'),
    ('separator', 'fg:gray'),
    ('instruction', 'fg:gray'),
])


# ============================================================================
# MODELOS DE DATOS
# ============================================================================
@dataclass
class MenuOption:
    """Opción de menú"""
    key: str
    label: str
    playbook: str
    description: str = ""
    requires_input: bool = False
    input_prompt: str = ""
    input_var_name: str = ""


@dataclass
class MenuCategory:
    """Categoría de menú"""
    key: str
    name: str
    icon: str
    options: List[MenuOption]


@dataclass
class ExecutionResult:
    """Resultado de ejecución de playbook"""
    success: bool
    data: Optional[Dict[str, Any]]
    stdout: str
    stderr: str
    returncode: int


# ============================================================================
# DEFINICIÓN DEL MENÚ COMPLETO
# ============================================================================
MENU_CATEGORIES = [
    # =========================================================================
    # [A] ADMIN & DOMINIO (NUEVO)
    # =========================================================================
    MenuCategory(
        key="A",
        name="Admin & Dominio",
        icon="🔐",
        options=[
            MenuOption("A1", "Desbloquear usuario de red (AD)", "admin/unlock_user.yml",
                      "Desbloquea una cuenta de usuario bloqueada en Active Directory",
                      requires_input=True, input_prompt="Username a desbloquear", input_var_name="ad_username"),
            MenuOption("A2", "Obtener password Admin Local (LAPS)", "admin/get_laps_password.yml",
                      "Obtiene la contraseña LAPS del administrador local desde AD"),
            MenuOption("A3", "Ver clave BitLocker Recovery (AD)", "admin/get_bitlocker_key.yml",
                      "Obtiene la clave de recuperación BitLocker (48 dígitos) desde AD"),
        ]
    ),
    # =========================================================================
    # [H] HARDWARE Y SISTEMA
    # =========================================================================
    MenuCategory(
        key="H",
        name="Hardware y Sistema",
        icon="💻",
        options=[
            MenuOption("H1", "Mostrar especificaciones", "hardware/specs.yml",
                      "Obtiene info del sistema: CPU, RAM, disco, red"),
            MenuOption("H2", "Terminar de configurar", "hardware/configure.yml",
                      "Ejecuta tareas de configuración inicial"),
            MenuOption("H3", "Optimizar sistema", "hardware/optimize.yml",
                      "Limpieza de disco, desfragmentación, etc."),
            MenuOption("H4", "Reiniciar equipo", "hardware/reboot.yml",
                      "Reinicia el equipo de forma controlada"),
            MenuOption("H5", "Actualizar drivers DELL", "hardware/dell_drivers.yml",
                      "Ejecuta Dell Command Update"),
            MenuOption("H6", "Activar Windows", "hardware/activate_windows.yml",
                      "Activa Windows con KMS"),
            MenuOption("H7", "Salud de Batería (Laptop)", "hardware/battery_health.yml",
                      "Genera reporte de salud de batería (solo laptops)"),
            MenuOption("H8", "Reporte SMART de Disco", "hardware/disk_smart.yml",
                      "Diagnóstico S.M.A.R.T. de discos duros y SSD"),
        ]
    ),
    # =========================================================================
    # [R] REDES Y CONECTIVIDAD
    # =========================================================================
    MenuCategory(
        key="R",
        name="Redes y Conectividad",
        icon="🌐",
        options=[
            MenuOption("R1", "WCORP Fix", "network/wcorp_fix.yml",
                      "Script WCORP + cleanDNS + gpupdate"),
            MenuOption("R2", "Analizador Wi-Fi", "network/wifi_analyzer.yml",
                      "Información detallada de conexión Wi-Fi, AP y señal"),
            MenuOption("R3", "Reparar red", "network/network_repair.yml",
                      "Flush DNS, reset IP, reiniciar adaptador"),
            MenuOption("R4", "Test de Velocidad", "network/speedtest.yml",
                      "Test de velocidad de Internet (descarga, latencia, jitter)"),
            MenuOption("R5", "Ver consumo de ancho de banda", "network/bandwidth_usage.yml",
                      "Estadísticas de uso de red en tiempo real"),
        ]
    ),
    # =========================================================================
    # [S] SOFTWARE
    # =========================================================================
    MenuCategory(
        key="S",
        name="Software",
        icon="📦",
        options=[
            MenuOption("S1", "Instalar Office 365", "software/install_office.yml",
                      "Instalación silenciosa de Office 365"),
            MenuOption("S2", "Reparar Office", "software/repair_office.yml",
                      "Ejecuta Quick Repair de Office"),
            MenuOption("S3", "Resetear OneDrive", "software/reset_onedrive.yml",
                      "Resetea OneDrive a su configuración inicial"),
            MenuOption("S4", "Gestionar aplicaciones", "software/manage_apps.yml",
                      "Listar, buscar y desinstalar aplicaciones"),
        ]
    ),
    # =========================================================================
    # [I] IMPRESORAS
    # =========================================================================
    MenuCategory(
        key="I",
        name="Impresoras",
        icon="🖨️",
        options=[
            MenuOption("I1", "Gestionar impresoras", "printers/manage_printers.yml",
                      "Gestión de spooler e impresoras"),
            MenuOption("I2", "Calibrar Zebra", "printers/zebra_calibrate.yml",
                      "Envía comando de calibración a impresora Zebra",
                      requires_input=True, input_prompt="IP de la impresora Zebra", input_var_name="zebra_ip"),
        ]
    ),
    # =========================================================================
    # [C] CONSOLA REMOTA
    # =========================================================================
    MenuCategory(
        key="C",
        name="Consola Remota",
        icon="🖥️",
        options=[
            MenuOption("C1", "Abrir consola remota", "remote/console.yml",
                      "Consola PowerShell interactiva"),
        ]
    ),
]


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================
def clear_screen():
    """Limpia la pantalla"""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_banner():
    """Muestra el banner de la aplicación"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██╗████████╗     ██████╗ ██████╗ ███████╗     ██████╗██╗     ██╗          ║
║   ██║╚══██╔══╝    ██╔═══██╗██╔══██╗██╔════╝    ██╔════╝██║     ██║          ║
║   ██║   ██║       ██║   ██║██████╔╝███████╗    ██║     ██║     ██║          ║
║   ██║   ██║       ██║   ██║██╔═══╝ ╚════██║    ██║     ██║     ██║          ║
║   ██║   ██║       ╚██████╔╝██║     ███████║    ╚██████╗███████╗██║          ║
║   ╚═╝   ╚═╝        ╚═════╝ ╚═╝     ╚══════╝     ╚═════╝╚══════╝╚═╝          ║
║                                                                              ║
║                    Automatización IT con Ansible                             ║
║                         v2.0 - Menú Expandido                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="cyan")


def show_menu_summary():
    """Muestra un resumen de las categorías disponibles"""
    table = Table(
        title="📋 Categorías Disponibles",
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED
    )
    table.add_column("Categoría", style="cyan", width=25)
    table.add_column("Opciones", style="green", justify="center", width=10)
    table.add_column("Descripción", style="white")
    
    descriptions = {
        "A": "Gestión de Active Directory: LAPS, BitLocker, usuarios",
        "H": "Specs, configuración, optimización, drivers, batería, disco",
        "R": "Wi-Fi, reparación de red, speedtest, bandwidth",
        "S": "Office, OneDrive, gestión de aplicaciones",
        "I": "Gestión de spooler e impresoras, Zebra",
        "C": "Consola PowerShell interactiva remota",
    }
    
    for cat in MENU_CATEGORIES:
        table.add_row(
            f"{cat.icon} [{cat.key}] {cat.name}",
            str(len(cat.options)),
            descriptions.get(cat.key, "")
        )
    
    console.print(table)
    console.print("")


def validate_hostname(hostname: str) -> bool:
    """
    Valida que el hostname sea seguro para usar.
    
    CRÍTICO: Nunca permitir 'all' sin confirmación explícita.
    """
    if not hostname or not hostname.strip():
        return False
    
    hostname = hostname.strip().lower()
    
    # Prohibir 'all' por seguridad
    if hostname == "all":
        console.print(Panel(
            "[red bold]ERROR: No se permite target_host='all' por seguridad[/red bold]\n\n"
            "[yellow]Esto podría ejecutar operaciones en TODOS los hosts del inventario.[/yellow]\n"
            "[dim]Si realmente necesitas ejecutar en múltiples hosts, agrégalos uno por uno.[/dim]",
            title="⚠️ Validación de Seguridad",
            border_style="red"
        ))
        return False
    
    return True


# ============================================================================
# FUNCIONES DE ANSIBLE
# ============================================================================
def check_online(hostname: str, vault_password: Optional[str] = None) -> bool:
    """
    Verifica si el host responde a WinRM antes de ejecutar tareas.
    
    Ejecuta ansible -m win_ping para verificar conectividad.
    Timeout corto (10 segundos) para respuesta rápida.
    
    Args:
        hostname: Hostname del equipo a verificar
        vault_password: Password del vault (opcional)
    
    Returns:
        bool: True si el host está online
    """
    if not validate_hostname(hostname):
        return False
    
    console.print(f"\n[cyan]🔍 Verificando conectividad con {hostname}...[/cyan]")
    
    env = os.environ.copy()
    env["ANSIBLE_STDOUT_CALLBACK"] = "json"
    env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    
    if vault_password:
        env["ANSIBLE_VAULT_PASSWORD"] = vault_password
    
    cmd = [
        "ansible",
        "-i", "inventory/hosts.ini",
        hostname,
        "-m", "win_ping"
    ]
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task(f"[cyan]Conectando a {hostname}...", total=None)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=15,
                cwd=str(BASE_DIR)
            )
        
        if result.returncode == 0:
            console.print(f"[green]✅ Host {hostname} online y accesible[/green]\n")
            return True
        else:
            console.print(Panel(
                f"[yellow]El host {hostname} no responde a WinRM[/yellow]\n\n"
                f"[dim]Verificar:\n"
                f"  • WinRM habilitado (Enable-PSRemoting -Force)\n"
                f"  • Puertos abiertos (5985/5986)\n"
                f"  • Firewall configurado\n"
                f"  • Hostname/IP correcta\n"
                f"  • Host en el inventario o accesible por nombre[/dim]\n\n"
                f"[red dim]Error: {result.stderr[:200] if result.stderr else 'Sin detalles'}[/red dim]",
                title=f"[red]❌ Host {hostname} Offline[/red]",
                border_style="red"
            ))
            return False
            
    except subprocess.TimeoutExpired:
        console.print(Panel(
            f"[yellow]Timeout conectando a {hostname}[/yellow]\n\n"
            "[dim]El host no respondió en 15 segundos.[/dim]",
            title=f"[red]⏱️ Timeout[/red]",
            border_style="red"
        ))
        return False
    except Exception as e:
        console.print(Panel(
            f"[red]Error ejecutando health check: {e}[/red]",
            title="Error",
            border_style="red"
        ))
        return False


def ejecutar_playbook(
    hostname: str,
    playbook_path: str,
    vault_password: Optional[str] = None,
    extra_vars: Optional[Dict[str, str]] = None,
    show_progress: bool = True
) -> ExecutionResult:
    """
    Ejecuta un playbook de Ansible y retorna resultados en JSON.
    
    Args:
        hostname: Hostname del equipo (validado que no sea 'all')
        playbook_path: Ruta al playbook relativa a playbooks/
        vault_password: Master password del vault (opcional)
        extra_vars: Variables extra para el playbook
        show_progress: Mostrar barra de progreso con Rich
    
    Returns:
        ExecutionResult: Resultado de la ejecución
    """
    # Validación de seguridad CRÍTICA
    if not validate_hostname(hostname):
        return ExecutionResult(
            success=False,
            data=None,
            stdout="",
            stderr="Hostname inválido o no permitido",
            returncode=1
        )
    
    # Construir path completo del playbook
    full_playbook_path = BASE_DIR / "playbooks" / playbook_path
    
    if not full_playbook_path.exists():
        console.print(Panel(
            f"[red]Playbook no encontrado: {playbook_path}[/red]\n\n"
            f"[dim]Ruta buscada: {full_playbook_path}[/dim]",
            title="Error",
            border_style="red"
        ))
        return ExecutionResult(
            success=False,
            data=None,
            stdout="",
            stderr=f"Playbook no encontrado: {playbook_path}",
            returncode=1
        )
    
    # Configurar entorno con JSON callback
    env = os.environ.copy()
    env["ANSIBLE_STDOUT_CALLBACK"] = "json"
    env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    
    if vault_password:
        env["ANSIBLE_VAULT_PASSWORD"] = vault_password
    
    # Construir comando
    cmd = [
        "ansible-playbook",
        "-i", "inventory/hosts.ini",
        str(full_playbook_path),
        "--extra-vars", f"target_host={hostname}"
    ]
    
    # Agregar variables extra
    if extra_vars:
        for key, value in extra_vars.items():
            cmd.extend(["--extra-vars", f"{key}={value}"])
    
    # Ejecutar con Progress bar de Rich
    result = None
    
    if show_progress:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task(
                f"[cyan]Ejecutando {playbook_path} en {hostname}...",
                total=None
            )
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=600,
                    cwd=str(BASE_DIR)
                )
            except subprocess.TimeoutExpired:
                console.print(Panel(
                    "[red]Timeout ejecutando playbook (10 minutos)[/red]",
                    title="Timeout",
                    border_style="red"
                ))
                return ExecutionResult(
                    success=False,
                    data=None,
                    stdout="",
                    stderr="Timeout",
                    returncode=1
                )
    else:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=600,
                cwd=str(BASE_DIR)
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                data=None,
                stdout="",
                stderr="Timeout",
                returncode=1
            )
    
    # Parsear JSON output
    json_data = None
    try:
        if result.stdout:
            # El JSON callback de Ansible devuelve todo el output como JSON
            json_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        # Si falla el parsing, intentar buscar JSON en el output
        pass
    
    return ExecutionResult(
        success=result.returncode == 0,
        data=json_data,
        stdout=result.stdout,
        stderr=result.stderr,
        returncode=result.returncode
    )


def mostrar_resultado(result: ExecutionResult, titulo: str = "Resultado"):
    """
    Muestra el resultado de una ejecución de forma formateada con Rich.
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
    
    # Si hay datos JSON, intentar mostrarlos en tabla
    if result.data:
        try:
            # Buscar datos en la estructura de Ansible JSON
            plays = result.data.get("plays", [])
            for play in plays:
                tasks = play.get("tasks", [])
                for task in tasks:
                    task_name = task.get("task", {}).get("name", "")
                    hosts = task.get("hosts", {})
                    for host, host_result in hosts.items():
                        # Mostrar mensajes de debug
                        if "msg" in host_result:
                            msg = host_result["msg"]
                            if isinstance(msg, list):
                                console.print(f"\n[cyan]{task_name}:[/cyan]")
                                for line in msg:
                                    if line:  # Skip empty lines
                                        console.print(f"  {line}")
                            else:
                                console.print(f"\n[cyan]{task_name}:[/cyan] {msg}")
                        # Mostrar stdout_lines
                        elif "stdout_lines" in host_result:
                            console.print(f"\n[cyan]{task_name}:[/cyan]")
                            for line in host_result["stdout_lines"]:
                                console.print(f"  {line}")
        except Exception:
            # Si falla el parsing, mostrar raw
            if result.stdout:
                console.print("\n[dim]Raw output:[/dim]")
                console.print(result.stdout[:2000])
    
    # Mostrar errores si hay
    if result.stderr and not result.success:
        console.print(f"\n[red]Errores:[/red]\n{result.stderr[:500]}")


def mostrar_specs_tabla(result: ExecutionResult, hostname: str):
    """
    Muestra las especificaciones del sistema en una tabla Rich.
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
    except Exception as e:
        console.print(f"[yellow]Error parseando datos: {e}[/yellow]")
        mostrar_resultado(result, f"Especificaciones - {hostname}")
        return
    
    console.print(table)


def mostrar_laps_resultado(result: ExecutionResult, hostname: str):
    """
    Muestra el resultado de LAPS de forma destacada.
    """
    if not result.success:
        mostrar_resultado(result, f"LAPS - {hostname}")
        return
    
    # Buscar el password en los datos
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
    """
    if not result.success:
        mostrar_resultado(result, f"BitLocker Recovery - {hostname}")
        return
    
    # Buscar claves en los datos
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


# ============================================================================
# FUNCIONES DE MENÚ
# ============================================================================
def solicitar_hostname() -> Optional[str]:
    """
    Solicita el hostname al usuario usando Questionary.
    """
    hostname = questionary.text(
        "Ingrese el hostname del equipo:",
        style=CUSTOM_STYLE,
        validate=lambda text: len(text.strip()) > 0 or "Debe ingresar un hostname"
    ).ask()
    
    if hostname is None:
        return None
    
    return hostname.strip().upper()


def solicitar_vault_password() -> Optional[str]:
    """
    Solicita la master password del Ansible Vault.
    Retorna None si el usuario cancela o presiona Enter vacío.
    """
    console.print("\n[dim]Si usas Ansible Vault, ingresa la master password.[/dim]")
    console.print("[dim]Presiona Enter para omitir (modo desarrollo).[/dim]\n")
    
    password = questionary.password(
        "Vault Password (opcional):",
        style=CUSTOM_STYLE
    ).ask()
    
    if password is None or password.strip() == "":
        return None
    
    return password


def mostrar_menu_categorias() -> Optional[MenuCategory]:
    """
    Muestra el menú de categorías y retorna la seleccionada.
    """
    choices = []
    for cat in MENU_CATEGORIES:
        choices.append(f"{cat.icon} [{cat.key}] {cat.name} ({len(cat.options)} opciones)")
    
    choices.append("───────────────────")
    choices.append("🔄 [0] Cambiar equipo")
    choices.append("❌ [X] Salir")
    
    answer = questionary.select(
        "Seleccione una categoría:",
        choices=choices,
        style=CUSTOM_STYLE,
        use_shortcuts=False
    ).ask()
    
    if answer is None or "Salir" in answer:
        return None
    
    if "Cambiar equipo" in answer:
        return MenuCategory(key="0", name="Cambiar", icon="", options=[])
    
    # Buscar categoría seleccionada
    for cat in MENU_CATEGORIES:
        if f"[{cat.key}]" in answer:
            return cat
    
    return None


def mostrar_menu_opciones(categoria: MenuCategory) -> Optional[MenuOption]:
    """
    Muestra las opciones de una categoría y retorna la seleccionada.
    """
    choices = []
    for opt in categoria.options:
        choices.append(f"[{opt.key}] {opt.label}")
    
    choices.append("───────────────────")
    choices.append("⬅️  Volver")
    
    answer = questionary.select(
        f"{categoria.icon} {categoria.name}:",
        choices=choices,
        style=CUSTOM_STYLE,
        use_shortcuts=False
    ).ask()
    
    if answer is None or "Volver" in answer:
        return None
    
    # Buscar opción seleccionada
    for opt in categoria.options:
        if f"[{opt.key}]" in answer:
            return opt
    
    return None


def ejecutar_opcion(
    opcion: MenuOption,
    hostname: str,
    vault_password: Optional[str] = None
):
    """
    Ejecuta una opción del menú.
    """
    console.print(f"\n[cyan]▶ Ejecutando: {opcion.label}[/cyan]")
    console.print(f"[dim]{opcion.description}[/dim]\n")
    
    extra_vars = {}
    
    # Si la opción requiere input adicional
    if opcion.requires_input:
        user_input = questionary.text(
            opcion.input_prompt + ":",
            style=CUSTOM_STYLE
        ).ask()
        
        if user_input is None:
            console.print("[yellow]Operación cancelada[/yellow]")
            return
        
        # Usar nombre de variable específico si está definido
        var_name = opcion.input_var_name if opcion.input_var_name else "user_input"
        extra_vars[var_name] = user_input
    
    # Confirmar ejecución
    if not questionary.confirm(
        f"¿Ejecutar '{opcion.label}' en {hostname}?",
        style=CUSTOM_STYLE,
        default=True
    ).ask():
        console.print("[yellow]Operación cancelada[/yellow]")
        return
    
    # Ejecutar playbook
    result = ejecutar_playbook(
        hostname=hostname,
        playbook_path=opcion.playbook,
        vault_password=vault_password,
        extra_vars=extra_vars if extra_vars else None
    )
    
    # Mostrar resultados según el tipo de opción
    if opcion.key == "H1":  # Specs
        mostrar_specs_tabla(result, hostname)
    elif opcion.key == "A2":  # LAPS
        mostrar_laps_resultado(result, hostname)
    elif opcion.key == "A3":  # BitLocker
        mostrar_bitlocker_resultado(result, hostname)
    else:
        mostrar_resultado(result, opcion.label)
    
    # Esperar antes de volver al menú
    console.print("")
    questionary.press_any_key_to_continue(
        "Presione cualquier tecla para continuar..."
    ).ask()


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================
def main():
    """
    Función principal de la aplicación.
    
    Flujo:
    1. Mostrar banner
    2. Solicitar vault password (opcional)
    3. Solicitar hostname
    4. Health check
    5. Loop de menú
    """
    try:
        clear_screen()
        show_banner()
        
        # Mostrar resumen del menú
        show_menu_summary()
        
        # Solicitar vault password (opcional)
        vault_password = solicitar_vault_password()
        
        while True:
            # Solicitar hostname
            hostname = solicitar_hostname()
            if hostname is None:
                console.print("\n[yellow]Saliendo...[/yellow]")
                break
            
            # Health check
            if not check_online(hostname, vault_password):
                if not questionary.confirm(
                    "¿Intentar con otro hostname?",
                    style=CUSTOM_STYLE,
                    default=True
                ).ask():
                    break
                continue
            
            # Mostrar info del host
            console.print(Panel(
                f"[green]Conectado a:[/green] [bold]{hostname}[/bold]",
                title="Host Activo",
                border_style="green"
            ))
            
            # Loop del menú
            while True:
                clear_screen()
                show_banner()
                console.print(f"[cyan]Host activo:[/cyan] [bold green]{hostname}[/bold green]\n")
                
                # Seleccionar categoría
                categoria = mostrar_menu_categorias()
                
                if categoria is None:
                    # Salir
                    break
                
                if categoria.key == "0":
                    # Cambiar equipo
                    break
                
                # Seleccionar opción
                opcion = mostrar_menu_opciones(categoria)
                
                if opcion is None:
                    # Volver al menú de categorías
                    continue
                
                # Ejecutar opción
                ejecutar_opcion(opcion, hostname, vault_password)
            
            # Preguntar si continuar con otro equipo
            if categoria is not None and categoria.key == "0":
                continue  # Cambiar equipo
            
            # Salir del programa
            break
        
        console.print("\n[green]¡Gracias por usar IT-Ops CLI![/green]\n")
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Programa interrumpido por el usuario[/yellow]\n")
    except Exception as e:
        console.print(Panel(
            f"[red]Error inesperado: {e}[/red]",
            title="Error",
            border_style="red"
        ))
        raise


if __name__ == "__main__":
    main()
