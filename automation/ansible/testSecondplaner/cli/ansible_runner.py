# -*- coding: utf-8 -*-
"""
cli/ansible_runner.py
=====================
Funciones de ejecución de Ansible mejoradas con soporte para segundo plano y nueva ventana.
"""

import os
import sys
import json
import subprocess
import shutil
import socket
import tempfile
import time
import threading
import platform
from typing import Optional, Dict, Tuple
from pathlib import Path

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .config import BASE_DIR, console, logger, MOCK_MODE
from .models import ExecutionResult, HostSnapshot


# ============================================================================
# CONFIGURACIÓN DE WINRM (para inventario dinámico)
# ============================================================================
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
    """Intenta resolver un hostname a una IP válida."""
    try:
        socket.inet_aton(hostname)
        return hostname, "Es una IP válida"
    except socket.error:
        pass
    
    try:
        result = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if result:
            ip = result[0][4][0]
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
    """Verifica que las dependencias del sistema estén instaladas."""
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
    """Valida que el hostname sea seguro para usar."""
    if not hostname or not hostname.strip():
        return False
    
    hostname = hostname.strip().lower()
    
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
    """Construye un inventario dinámico en formato INI para un host."""
    if not resolved_ip:
        my_hostname = socket.gethostname().lower()
        if hostname.lower() in [my_hostname, "localhost", "127.0.0.1", "127.0.1.1"]:
            gateway = _get_wsl_gateway()
            if gateway:
                resolved_ip = gateway
                logger.info(f"Target es local, forzando IP de Gateway: {gateway}")
        
        if not resolved_ip:
            resolved_ip, msg = _resolve_hostname(hostname)
            
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
    
    if resolved_ip and resolved_ip != hostname:
        lines.append(f"ansible_host={resolved_ip}")
    
    for key, value in DEFAULT_WINRM_VARS.items():
        lines.append(f"{key}={value}")
    
    return "\n".join(lines)


def obtener_host_snapshot(hostname: str, vault_password: Optional[str] = None) -> Optional[HostSnapshot]:
    """Obtiene información rápida del host (Usuario, OS, Disco)."""
    env = os.environ.copy()
    env["ANSIBLE_STDOUT_CALLBACK"] = "json"
    env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    if vault_password:
        env["ANSIBLE_VAULT_PASSWORD"] = vault_password

    ps_script = (
        "$user = (Get-CimInstance Win32_ComputerSystem).UserName; "
        "$os = (Get-CimInstance Win32_OperatingSystem).Caption; "
        "$disk = Get-CimInstance Win32_LogicalDisk -Filter \\\"DeviceID='C:'\\\"; "
        "$free = [math]::round($disk.FreeSpace / 1GB, 1); "
        "$total = [math]::round($disk.Size / 1GB, 1); "
        "@{ user=$user; os=$os; disk_free=$free; disk_total=$total } | ConvertTo-Json"
    )

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
    """Verifica si el host responde a WinRM antes de ejecutar tareas."""
    if not validate_hostname(hostname):
        return False
    
    console.print(f"\n[cyan]🔍 Verificando conectividad con {hostname}...[/cyan]")
    
    env = os.environ.copy()
    env["ANSIBLE_STDOUT_CALLBACK"] = "json"
    env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    
    if vault_password:
        env["ANSIBLE_VAULT_PASSWORD"] = vault_password
    
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
            error_msg = result.stderr.strip() if result.stderr else ""
            if not error_msg and result.stdout:
                if "msg" in result.stdout:
                    try:
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
        if os.path.exists(inventory_file.name):
            os.unlink(inventory_file.name)


def ejecutar_playbook_nueva_ventana(
    hostname: str,
    playbook_path: str,
    vault_password: Optional[str] = None,
    extra_vars: Optional[Dict[str, str]] = None
) -> ExecutionResult:
    """
    Ejecuta un playbook en una nueva ventana/terminal (para consolas interactivas).
    
    Args:
        hostname: Hostname del equipo
        playbook_path: Ruta al playbook relativa a playbooks/
        vault_password: Password del vault (opcional)
        extra_vars: Variables extra para el playbook
        
    Returns:
        ExecutionResult: Resultado de la ejecución
    """
    if not validate_hostname(hostname):
        return ExecutionResult(False, None, "", "Hostname inválido", 1)
    
    # Manejar rutas relativas y absolutas
    if playbook_path.startswith("playbooks/"):
        full_playbook_path = BASE_DIR / playbook_path
    else:
        full_playbook_path = BASE_DIR / "playbooks" / playbook_path
    
    if not full_playbook_path.exists():
        logger.error(f"Playbook no encontrado: {full_playbook_path}")
        return ExecutionResult(False, None, "", f"Playbook no encontrado: {playbook_path}", 1)

    env = os.environ.copy()
    env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    if vault_password:
        env["ANSIBLE_VAULT_PASSWORD"] = vault_password

    inventory_content = _build_dynamic_inventory(hostname)
    cache_dir = BASE_DIR / ".cache"
    cache_dir.mkdir(exist_ok=True)
    inventory_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.ini', dir=str(cache_dir), delete=False
    )
    inventory_file.write(inventory_content)
    inventory_file.close()
    
    cmd = [
        "ansible-playbook",
        "-i", inventory_file.name,
        str(full_playbook_path),
        "--extra-vars", f"target_host={hostname}"
    ]
    
    if extra_vars:
        for key, value in extra_vars.items():
            cmd.extend(["--extra-vars", f"{key}={value}"])

    vault_file = None
    if vault_password:
        vault_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        vault_file.write(vault_password)
        vault_file.close()
        cmd.extend(["--vault-password-file", vault_file.name])

    # Abrir en nueva ventana según el OS
    if platform.system() == "Windows":
        # PowerShell en nueva ventana
        ps_script = f"""
$env:ANSIBLE_HOST_KEY_CHECKING='False'
if ('{vault_password}') {{ $env:ANSIBLE_VAULT_PASSWORD='{vault_password}' }}
cd '{BASE_DIR}'
{' '.join(cmd)}
Write-Host "`nPresiona cualquier tecla para cerrar..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
"""
        subprocess.Popen([
            "powershell", "-NoExit", "-Command", ps_script
        ], cwd=str(BASE_DIR))
        
        console.print(f"\n[green]✅ Abriendo consola remota en nueva ventana...[/green]\n")
        return ExecutionResult(True, None, "Consola abierta en nueva ventana", "", 0)
    else:
        # Linux/Mac: usar xterm, gnome-terminal, etc.
        term = os.environ.get("TERMINAL", "xterm")
        if shutil.which(term):
            subprocess.Popen([
                term, "-e", "bash", "-c",
                f"cd '{BASE_DIR}' && {' '.join(cmd)}; read -p 'Press Enter to close...'"
            ])
            console.print(f"\n[green]✅ Abriendo consola remota en nueva ventana...[/green]\n")
            return ExecutionResult(True, None, "Consola abierta en nueva ventana", "", 0)
        else:
            # Fallback: ejecutar normalmente
            return ejecutar_playbook(hostname, playbook_path, vault_password, extra_vars, interactive=True)


def ejecutar_playbook_mock(
    hostname: str,
    playbook_path: str,
    vault_password: Optional[str] = None,
    extra_vars: Optional[Dict[str, str]] = None,
    show_progress: bool = True
) -> ExecutionResult:
    """
    Simula la ejecución de un playbook (mock para pruebas de UI).
    
    Genera resultados aleatorios (70% éxito, 30% error) con duración
    realista según el tipo de tarea.
    
    Args:
        hostname: Hostname del equipo
        playbook_path: Ruta al playbook
        vault_password: Password del vault (ignorado en mock)
        extra_vars: Variables extra (ignoradas parcialmente en mock)
        show_progress: Mostrar barra de progreso (ignorado en mock)
        
    Returns:
        ExecutionResult: Resultado simulado de la ejecución
    """
    import random
    import time
    
    # Determinar duración según tipo de playbook
    playbook_name = playbook_path.lower()
    if any(x in playbook_name for x in ["specs", "list", "check", "info"]):
        # Read-only rápido: 2-5 segundos
        duration = random.uniform(2.0, 5.0)
    elif any(x in playbook_name for x in ["query", "status", "audit"]):
        # Consultas: 3-8 segundos
        duration = random.uniform(3.0, 8.0)
    elif any(x in playbook_name for x in ["install", "configure", "optimize"]):
        # Instalaciones/Tareas largas: 10-30 segundos
        duration = random.uniform(10.0, 30.0)
    else:
        # Modificaciones: 5-15 segundos
        duration = random.uniform(5.0, 15.0)
    
    # Simular ejecución esperando
    time.sleep(min(duration, 0.5))  # Solo esperar 0.5s máximo para UI
    
    # 70% éxito, 30% error
    success = random.random() > 0.3
    
    # Generar datos mock según tipo de playbook
    mock_data = None
    stdout = ""
    
    if success:
        if "specs" in playbook_name:
            mock_data = {
                "plays": [{
                    "tasks": [{
                        "hosts": {
                            hostname: {
                                "ansible_facts": {
                                    "system_specs": {
                                        "processor": "Intel Core i7-10750H @ 2.60GHz",
                                        "memory_ram": "16 GB",
                                        "disk_c": "512 GB SSD",
                                        "disk_free": "350 GB",
                                        "os": "Windows 11 Pro",
                                        "os_version": "10.0.22621"
                                    }
                                }
                            }
                        }
                    }]
                }]
            }
            stdout = f"✅ Especificaciones obtenidas para {hostname}"
        elif "list_apps" in playbook_name or "apps" in playbook_name:
            mock_data = {
                "plays": [{
                    "tasks": [{
                        "hosts": {
                            hostname: {
                                "stdout_lines": [
                                    "Microsoft Office 365",
                                    "Google Chrome",
                                    "Visual Studio Code",
                                    "7-Zip",
                                    "Notepad++"
                                ]
                            }
                        }
                    }]
                }]
            }
            stdout = f"✅ Lista de aplicaciones obtenida para {hostname}"
        elif "laps" in playbook_name:
            mock_data = {
                "plays": [{
                    "tasks": [{
                        "hosts": {
                            hostname: {
                                "msg": [
                                    f"Password: {''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=12))}",
                                    "Expira: 2025-12-31"
                                ]
                            }
                        }
                    }]
                }]
            }
            stdout = f"✅ Password LAPS obtenido para {hostname}"
        elif "bitlocker" in playbook_name:
            mock_data = {
                "plays": [{
                    "tasks": [{
                        "hosts": {
                            hostname: {
                                "msg": [
                                    f"Recovery Password: {''.join(random.choices('0123456789', k=48))}"
                                ]
                            }
                        }
                    }]
                }]
            }
            stdout = f"✅ Clave BitLocker obtenida para {hostname}"
        else:
            stdout = f"✅ Operación completada exitosamente para {hostname}"
    else:
        error_msg = random.choice([
            "Connection timeout",
            "Permission denied",
            "Host unreachable",
            "WinRM error: HTTP 500",
            "Ansible module failed"
        ])
        stderr = f"❌ Error: {error_msg}"
        return ExecutionResult(
            success=False,
            data=None,
            stdout="",
            stderr=stderr,
            returncode=1,
            duration=duration
        )
    
    return ExecutionResult(
        success=True,
        data=mock_data,
        stdout=stdout,
        stderr="",
        returncode=0,
        duration=duration
    )


def ejecutar_playbook(
    hostname: str,
    playbook_path: str,
    vault_password: Optional[str] = None,
    extra_vars: Optional[Dict[str, str]] = None,
    show_progress: bool = True,
    interactive: bool = False,
    background: bool = False
) -> ExecutionResult:
    """
    Ejecuta un playbook de Ansible con soporte para segundo plano.
    
    Args:
        hostname: Hostname del equipo
        playbook_path: Ruta al playbook relativa a playbooks/
        vault_password: Password del vault (opcional)
        extra_vars: Variables extra para el playbook
        show_progress: Mostrar barra de progreso con Rich
        interactive: Si es True, no captura output para permitir interacción
        background: Si es True, ejecuta en segundo plano (retorna job_id)
        
    Returns:
        ExecutionResult: Objeto con los resultados de la ejecución
    """
    if not validate_hostname(hostname):
        return ExecutionResult(False, None, "", "Hostname inválido", 1)
    
    # Manejar rutas relativas y absolutas
    if playbook_path.startswith("playbooks/"):
        full_playbook_path = BASE_DIR / playbook_path
    else:
        full_playbook_path = BASE_DIR / "playbooks" / playbook_path
    
    if not full_playbook_path.exists() and not MOCK_MODE:
        logger.error(f"Playbook no encontrado: {full_playbook_path}")
        return ExecutionResult(False, None, "", f"Playbook no encontrado: {playbook_path}", 1)

    # Si está en modo mock, usar función mock
    if MOCK_MODE:
        return ejecutar_playbook_mock(hostname, playbook_path, vault_password, extra_vars, show_progress)

    # Si es background, usar BackgroundEngine
    if background:
        from core.engine import BackgroundEngine
        engine = BackgroundEngine()
        job_id = engine.launch_playbook(str(full_playbook_path), hostname, extra_vars)
        return ExecutionResult(True, None, f"Job {job_id} iniciado", "", 0, job_id=job_id, is_background=True)

    # Modo normal (síncrono)
    env = os.environ.copy()
    env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    if not interactive:
        env["ANSIBLE_STDOUT_CALLBACK"] = "json"
    
    inventory_content = _build_dynamic_inventory(hostname)
    cache_dir = BASE_DIR / ".cache"
    cache_dir.mkdir(exist_ok=True)
    inventory_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.ini', dir=str(cache_dir), delete=False
    )
    inventory_file.write(inventory_content)
    inventory_file.close()
    
    cmd = [
        "ansible-playbook",
        "-i", inventory_file.name,
        str(full_playbook_path),
        "--extra-vars", f"target_host={hostname}"
    ]
    
    if extra_vars:
        for key, value in extra_vars.items():
            cmd.extend(["--extra-vars", f"{key}={value}"])

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
        
        if result_proc.stdout:
            logger.debug(f"STDOUT: {result_proc.stdout[:500]}...")
        if result_proc.stderr:
            logger.error(f"STDERR: {result_proc.stderr}")

        json_data = None
        if result_proc.stdout:
            try:
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
        if os.path.exists(inventory_file.name):
            os.unlink(inventory_file.name)
        if vault_file and os.path.exists(vault_file.name):
            os.unlink(vault_file.name)
