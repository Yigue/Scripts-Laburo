# -*- coding: utf-8 -*-
"""
cli/ansible_runner.py
=====================
Funciones de ejecución de Ansible.

Contiene:
- check_environment(): Verifica dependencias del sistema
- validate_hostname(): Valida que el hostname sea seguro
- check_online(): Verifica conectividad WinRM
- ejecutar_playbook(): Ejecuta un playbook de Ansible

IMPORTANTE: Este módulo usa inventario dinámico para permitir
conectarse a cualquier hostname sin necesidad de agregarlo
manualmente al archivo hosts.ini.
"""

import os
import sys
import json
import subprocess
import shutil
import socket
import tempfile
import time
import questionary
from typing import Optional, Dict, Tuple

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .config import BASE_DIR, console, logger
from .models import ExecutionResult, HostSnapshot


# ============================================================================
# CONFIGURACIÓN DE WINRM (para inventario dinámico)
# ============================================================================
# Estas variables se usan cuando se conecta a un host que no está en el
# inventario estático. Puedes ajustar estos valores según tu entorno.
DEFAULT_WINRM_VARS = {
    "ansible_connection": "winrm",
    "ansible_winrm_transport": "ntlm",
    "ansible_winrm_scheme": "http",
    "ansible_port": "5985",
    "ansible_winrm_server_cert_validation": "ignore",
    "ansible_shell_type": "powershell",
    "ansible_user": "{{ vault_ansible_user }}",
    "ansible_password": "{{ vault_ansible_password }}",
}


# ============================================================================
# FUNCIONES DE RESOLUCIÓN DE RED
# ============================================================================
def _get_wsl_gateway() -> Optional[str]:
    """Obtiene la IP del gateway de WSL (Windows host)."""
    try:
        result = subprocess.check_output(
            "ip route show | grep default | awk '{print $3}'",
            shell=True, stderr=subprocess.DEVNULL
        ).decode().strip()
        return result if result else None
    except Exception:
        return None


def _resolve_hostname(hostname: str) -> Tuple[Optional[str], str]:
    """
    Intenta resolver un hostname a una IP válida.
    
    Detecta si el hostname resuelve a localhost (problema común en WSL)
    y sugiere alternativas.
    
    Args:
        hostname: El hostname a resolver
        
    Returns:
        Tuple (ip, mensaje): IP resuelta o None, y mensaje descriptivo
    """
    # Si ya es una IP, retornarla
    try:
        socket.inet_aton(hostname)
        return hostname, "Es una IP válida"
    except socket.error:
        pass
    
    # Intentar resolver con socket
    try:
        result = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if result:
            ip = result[0][4][0]
            # Verificar que no sea localhost
            if ip.startswith("127.") or ip == "::1":
                return None, f"DNS resuelve a localhost ({ip})"
            return ip, f"Resuelto vía DNS a {ip}"
    except socket.gaierror:
        pass
    
    return None, "No se pudo resolver el hostname"


def _test_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """Verifica si un puerto está abierto en un host."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def check_environment():
    """
    Verifica que las dependencias del sistema estén instaladas.
    
    Busca los binarios de Ansible (ansible, ansible-playbook) en el PATH.
    Si faltan, muestra un mensaje de error y termina la ejecución.
    """
    missing = []
    
    for cmd in ["ansible", "ansible-playbook"]:
        if not shutil.which(cmd):
            missing.append(cmd)
            
    if missing:
        console.print(Panel(
            f"[red bold]Error: Faltan dependencias del sistema[/red bold]\n\n"
            f"No se encontraron los siguientes comandos: {', '.join(missing)}\n"
            "[yellow]Asegúrate de tener Ansible instalado y en tu PATH.[/yellow]",
            title="⚠️ Error de Entorno",
            border_style="red"
        ))
        sys.exit(1)


def validate_hostname(hostname: str) -> bool:
    """
    Valida que el hostname sea seguro para usar.
    
    CRÍTICO: Nunca permitir 'all' sin confirmación explícita ya que
    podría ejecutar operaciones en TODOS los hosts del inventario.
    
    Args:
        hostname: El hostname a validar
        
    Returns:
        bool: True si el hostname es válido y seguro
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


def _build_dynamic_inventory(hostname: str, resolved_ip: Optional[str] = None) -> str:
    """
    Construye un inventario dinámico en formato INI para un host.
    
    Este inventario permite conectarse a cualquier hostname sin
    necesidad de tenerlo en el archivo hosts.ini estático.
    
    Si resolved_ip está disponible, usa ansible_host para dirigir
    la conexión a esa IP en lugar de depender del DNS local.
    
    Args:
        hostname: El hostname o IP del equipo
        resolved_ip: IP resuelta (opcional, para evitar problemas DNS)
        
    Returns:
        str: Contenido del inventario en formato INI
    """
    # Si no tenemos IP resuelta, intentar resolver
    if not resolved_ip:
        # TRUCO: Si el hostname ingresado es el de tu propia máquina, 
        # forzamos el uso de la IP del Gateway de WSL automáticamente.
        my_hostname = socket.gethostname().lower()
        if hostname.lower() in [my_hostname, "localhost", "127.0.0.1", "127.0.1.1"]:
            gateway = _get_wsl_gateway()
            if gateway:
                resolved_ip = gateway
                logger.info(f"Target es local, forzando IP de Gateway: {gateway}")
        
        # Si aún no hay IP, intentar resolver normalmente
        if not resolved_ip:
            resolved_ip, msg = _resolve_hostname(hostname)
            
            # Si el DNS falla (resuelve a localhost), intentar con el gateway como último recurso
            if not resolved_ip:
                gateway = _get_wsl_gateway()
                if gateway and _test_port(gateway, 5985):
                    logger.info(f"DNS resuelve mal para {hostname}, usando gateway WSL: {gateway}")
                    resolved_ip = gateway
    
    lines = [
        "[target]",
        hostname,
        "",
        "[windows_hosts:children]",
        "target",
        "",
        "[target:vars]",
    ]
    
    # Agregar ansible_host si tenemos una IP válida diferente al hostname
    if resolved_ip and resolved_ip != hostname:
        lines.append(f"ansible_host={resolved_ip}")
    
    for key, value in DEFAULT_WINRM_VARS.items():
        lines.append(f"{key}={value}")
    
    return "\n".join(lines)


def obtener_host_snapshot(hostname: str, vault_password: Optional[str] = None) -> Optional[HostSnapshot]:
    """
    Obtiene información rápida del host (Usuario, OS, Disco).
    
    Se ejecuta como un paso rápido tras verificar que el host está online.
    """
    env = os.environ.copy()
    env["ANSIBLE_STDOUT_CALLBACK"] = "json"
    env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    if vault_password:
        env["ANSIBLE_VAULT_PASSWORD"] = vault_password

    # PowerShell para obtener Snapshot rápido
    ps_script = (
        "$user = (Get-CimInstance Win32_ComputerSystem).UserName; "
        "$os = (Get-CimInstance Win32_OperatingSystem).Caption; "
        "$disk = Get-CimInstance Win32_LogicalDisk -Filter \\\"DeviceID='C:'\\\"; "
        "$free = [math]::round($disk.FreeSpace / 1GB, 1); "
        "$total = [math]::round($disk.Size / 1GB, 1); "
        "@{ user=$user; os=$os; disk_free=$free; disk_total=$total } | ConvertTo-Json"
    )

    inventory_content = _build_dynamic_inventory(hostname)
    # Crear inventario en .cache/ para que Ansible encuentre group_vars/
    cache_dir = BASE_DIR / ".cache"
    cache_dir.mkdir(exist_ok=True)
    inventory_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.ini', dir=str(cache_dir), delete=False
    )
    inventory_file.write(inventory_content)
    inventory_file.close()

    cmd = [
        "ansible",
        "-i", inventory_file.name,
        hostname,
        "-m", "win_shell",
        "-a", ps_script
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, env=env, timeout=30, cwd=str(BASE_DIR)
        )
        if result.returncode == 0:
            output = result.stdout
            if "{" in output:
                json_start = output.find("{")
                json_end = output.rfind("}") + 1
                data = json.loads(output[json_start:json_end])
                
                # Extraer de la estructura de Ansible
                if "plays" in data:
                    res = data["plays"][0]["tasks"][0]["hosts"][hostname]
                    if "stdout" in res:
                        shot = json.loads(res["stdout"])
                        return HostSnapshot(
                            hostname=hostname,
                            user=shot.get("user", "N/A"),
                            os=shot.get("os", "N/A"),
                            disk_free=shot.get("disk_free", 0),
                            disk_total=shot.get("disk_total", 0)
                        )
    except Exception as e:
        logger.error(f"Error obteniendo snapshot: {e}")
    finally:
        if os.path.exists(inventory_file.name):
            os.unlink(inventory_file.name)
    
    return None


def check_online(hostname: str, vault_password: Optional[str] = None) -> bool:
    """
    Verifica si el host responde a WinRM antes de ejecutar tareas.
    
    Ejecuta ansible -m win_ping para verificar conectividad.
    Usa inventario dinámico para no depender del archivo estático.
    
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
    
    # Crear inventario dinámico temporal en .cache/
    inventory_content = _build_dynamic_inventory(hostname)
    cache_dir = BASE_DIR / ".cache"
    cache_dir.mkdir(exist_ok=True)
    inventory_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.ini', dir=str(cache_dir), delete=False
    )
    inventory_file.write(inventory_content)
    inventory_file.close()
    
    cmd = [
        "ansible",
        "-i", inventory_file.name,
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
            # Intentar extraer error de stdout si stderr está vacío (común en Ansible)
            error_msg = result.stderr.strip() if result.stderr else ""
            if not error_msg and result.stdout:
                if "msg" in result.stdout:
                    try:
                        import json
                        data = json.loads(result.stdout)
                        error_msg = data.get("plays", [{}])[0].get("tasks", [{}])[0].get("hosts", {}).get(hostname, {}).get("msg", "")
                    except:
                        error_msg = result.stdout[:200].strip()
                else:
                    error_msg = result.stdout[:200].strip()

            console.print(Panel(
                f"[yellow]El host {hostname} no responde a WinRM[/yellow]\n\n"
                f"[dim]Verificar:\n"
                f"  • WinRM habilitado (Enable-PSRemoting -Force)\n"
                f"  • Puertos abiertos (5985/5986)\n"
                f"  • Firewall configurado\n"
                f"  • Hostname/IP correcta\n"
                f"  • Resolución DNS funciona[/dim]\n\n"
                f"[red dim]Error: {error_msg if error_msg else 'Sin detalles'}[/red dim]",
                title=f"[red]❌ Host {hostname} Offline[/red]",
                border_style="red"
            ))
            
            # Si el host es localhost o NB102237, ofrecer reparación
            my_hostname = socket.gethostname().lower()
            if hostname.lower() in [my_hostname, "localhost", "127.0.0.1"]:
                if questionary.confirm("¿Deseas ver los comandos para reparar WinRM localmente?", default=True).ask():
                    repair_winrm_local()
                    
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
    finally:
        # Limpiar inventario temporal
        if os.path.exists(inventory_file.name):
            os.unlink(inventory_file.name)


def ejecutar_playbook(
    hostname: str,
    playbook_path: str,
    vault_password: Optional[str] = None,
    extra_vars: Optional[Dict[str, str]] = None,
    show_progress: bool = True,
    interactive: bool = False
) -> ExecutionResult:
    """
    Ejecuta un playbook de Ansible con inventario dinámico.
    
    Args:
        hostname: Hostname del equipo
        playbook_path: Ruta al playbook relativa a playbooks/
        vault_password: Password del vault (opcional)
        extra_vars: Variables extra para el playbook
        show_progress: Mostrar barra de progreso con Rich
        interactive: Si es True, no captura output para permitir interacción
        
    Returns:
        ExecutionResult: Objeto con los resultados de la ejecución
    """
    if not validate_hostname(hostname):
        return ExecutionResult(False, None, "", "Hostname inválido", 1)
    
    full_playbook_path = BASE_DIR / "playbooks" / playbook_path
    if not full_playbook_path.exists():
        logger.error(f"Playbook no encontrado: {full_playbook_path}")
        return ExecutionResult(False, None, "", f"Playbook no encontrado: {playbook_path}", 1)

    # Configurar entorno
    env = os.environ.copy()
    env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    if not interactive:
        env["ANSIBLE_STDOUT_CALLBACK"] = "json"
    
    # Crear inventario dinámico temporal en .cache/
    inventory_content = _build_dynamic_inventory(hostname)
    cache_dir = BASE_DIR / ".cache"
    cache_dir.mkdir(exist_ok=True)
    inventory_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.ini', dir=str(cache_dir), delete=False
    )
    inventory_file.write(inventory_content)
    inventory_file.close()
    
    # Construir comando base con inventario dinámico
    cmd = [
        "ansible-playbook",
        "-i", inventory_file.name,
        str(full_playbook_path),
        "--extra-vars", f"target_host={hostname}"
    ]
    
    # Agregar variables extra
    if extra_vars:
        for key, value in extra_vars.items():
            cmd.extend(["--extra-vars", f"{key}={value}"])
    
    # Manejo de Vault mediante archivo temporal
    vault_file = None
    if vault_password:
        vault_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        vault_file.write(vault_password)
        vault_file.close()
        cmd.extend(["--vault-password-file", vault_file.name])

    logger.info(f"Ejecutando: {' '.join([c for c in cmd if 'password' not in c.lower()])}")

    start_time = time.time()
    try:
        if interactive:
            # En modo interactivo, ejecutamos directamente para que el usuario vea/escriba en la consola
            result_proc = subprocess.run(cmd, cwd=str(BASE_DIR), env=env)
            duration = time.time() - start_time
            return ExecutionResult(
                success=result_proc.returncode == 0,
                data=None,
                stdout="Ejecución interactiva completada",
                stderr="",
                returncode=result_proc.returncode,
                duration=duration
            )

        # Modo normal con progreso
        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console,
                transient=True
            ) as progress:
                progress.add_task(f"[cyan]Ejecutando {playbook_path} en {hostname}...", total=None)
                result_proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=1200, cwd=str(BASE_DIR))
        else:
            result_proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=1200, cwd=str(BASE_DIR))

        duration = time.time() - start_time
        
        # Registrar logs
        if result_proc.stdout:
            logger.debug(f"STDOUT: {result_proc.stdout[:500]}...")
        if result_proc.stderr:
            logger.error(f"STDERR: {result_proc.stderr}")

        # Parsear JSON
        json_data = None
        if result_proc.stdout:
            try:
                # Buscar el bloque JSON balanceado
                output = result_proc.stdout
                if "{" in output and "}" in output:
                    json_start = output.find("{")
                    json_end = output.rfind("}") + 1
                    json_str = output[json_start:json_end]
                    json_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"No se pudo parsear el output como JSON: {e}")
                if result_proc.returncode != 0:
                    logger.error(f"Error de ejecución sin JSON válido. Return code: {result_proc.returncode}")

        return ExecutionResult(
            success=result_proc.returncode == 0,
            data=json_data,
            stdout=result_proc.stdout,
            stderr=result_proc.stderr,
            returncode=result_proc.returncode,
            duration=duration
        )

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.error(f"Timeout en playbook: {playbook_path}")
        return ExecutionResult(False, None, "", "Timeout de ejecución (20 min)", 1, duration)
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error inesperado ejecutando playbook: {e}")
        return ExecutionResult(False, None, "", str(e), 1, duration)
    finally:
        # Limpiar archivos temporales
        if os.path.exists(inventory_file.name):
            os.unlink(inventory_file.name)
        if vault_file and os.path.exists(vault_file.name):
            os.unlink(vault_file.name)


def repair_winrm_local():
    """Muestra los comandos para reparar WinRM en la máquina local."""
    repair_cmds = [
        "Enable-PSRemoting -Force",
        "Set-NetConnectionProfile -NetworkCategory Private",
        "winrm quickconfig -q",
        "winrm set winrm/config/service '@{AllowUnencrypted=\"true\"}'",
        "winrm set winrm/config/service/auth '@{Basic=\"true\"}'",
        "New-NetFirewallRule -DisplayName \"WSL to WinRM\" -Direction Inbound -LocalPort 5985 -Protocol TCP -Action Allow -RemoteAddress 172.27.144.0/24"
    ]
    
    console.print(Panel(
        "\n".join([f"[bold cyan]{c}[/bold cyan]" for c in repair_cmds]),
        title="🛠️ Reparación de WinRM (PowerShell Admin)",
        border_style="yellow"
    ))
    console.print("\n[yellow]Copia y pega estos comandos en una consola de PowerShell con privilegios de Administrador.[/yellow]\n")
