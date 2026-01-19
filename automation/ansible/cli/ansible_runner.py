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
import platform
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
# FUNCIONES AUXILIARES
# ============================================================================
def _decrypt_vault_vars(vault_password: Optional[str] = None) -> Dict[str, str]:
    """
    Descifra el archivo vault.yml y retorna un diccionario con las variables.
    
    Args:
        vault_password: Password del vault (opcional)
        
    Returns:
        Dict con las variables del vault (vault_ansible_user, vault_ansible_password, etc.)
        o diccionario vacío si no se puede descifrar
    """
    if not vault_password:
        return {}
    
    vault_file = BASE_DIR / "inventory" / "group_vars" / "all" / "vault.yml"
    if not vault_file.exists():
        logger.warning("Archivo vault.yml no encontrado")
        return {}
    
    try:
        # Usar ansible-vault view para leer contenido descifrado
        vault_pass_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        vault_pass_file.write(vault_password)
        vault_pass_file.close()
        
        cmd = [
            "ansible-vault",
            "view",
            "--vault-password-file", vault_pass_file.name,
            str(vault_file)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(BASE_DIR)
        )
        
        # Limpiar archivo temporal de password
        if os.path.exists(vault_pass_file.name):
            os.unlink(vault_pass_file.name)
        
        if result.returncode != 0:
            logger.warning(f"No se pudo descifrar vault: {result.stderr}")
            #region agent log
            log_path = "/home/korg/Scripts-Laburo/automation/ansible/.cursor/debug.log"
            try:
                with open(log_path, "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "cli/ansible_runner.py:101", "message": "Error descifrando vault", "data": {"returncode": result.returncode, "stderr": result.stderr[:200]}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
            #endregion
            return {}
        
        # Verificar si el output está vacío o solo tiene whitespace
        if not result.stdout or not result.stdout.strip():
            logger.warning("Vault descifrado está vacío - no hay variables definidas")
            #region agent log
            log_path = "/home/korg/Scripts-Laburo/automation/ansible/.cursor/debug.log"
            try:
                with open(log_path, "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "cli/ansible_runner.py:105", "message": "Vault vacío", "data": {"stdout_length": len(result.stdout) if result.stdout else 0}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
            #endregion
            return {}
        
        # Parsear YAML del output
        import yaml
        try:
            vault_vars = yaml.safe_load(result.stdout)
            #region agent log
            log_path = "/home/korg/Scripts-Laburo/automation/ansible/.cursor/debug.log"
            try:
                with open(log_path, "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "cli/ansible_runner.py:115", "message": "Vault descifrado", "data": {"has_vars": vault_vars is not None, "keys": list(vault_vars.keys()) if vault_vars else [], "has_user": "vault_ansible_user" in (vault_vars or {}), "has_password": "vault_ansible_password" in (vault_vars or {}), "stdout_preview": result.stdout[:200]}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
            #endregion
            if vault_vars and isinstance(vault_vars, dict):
                return vault_vars
        except Exception as e:
            logger.warning(f"Error parseando vault YAML: {e}")
            #region agent log
            log_path = "/home/korg/Scripts-Laburo/automation/ansible/.cursor/debug.log"
            try:
                with open(log_path, "a") as f:
                    import json
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "cli/ansible_runner.py:119", "message": "Error parseando vault YAML", "data": {"error": str(e), "stdout_preview": result.stdout[:200] if result.stdout else None}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
            #endregion
            return {}
            
    except Exception as e:
        logger.error(f"Error descifrando vault: {e}")
        #region agent log
        log_path = "/home/korg/Scripts-Laburo/automation/ansible/.cursor/debug.log"
        try:
            with open(log_path, "a") as f:
                import json
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "cli/ansible_runner.py:115", "message": "Excepción en descifrado vault", "data": {"error_type": type(e).__name__, "error_msg": str(e)}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except: pass
        #endregion
        return {}
    
    return {}


def _ensure_cache_setup():
    """
    Prepara el directorio .cache y asegura que group_vars esté accessible.
    
    Esto es necesario porque al usar un inventario temporal en .cache/,
    Ansible busca group_vars en .cache/group_vars por defecto.
    """
    cache_dir = BASE_DIR / ".cache"
    cache_dir.mkdir(exist_ok=True)
    
    # Symlink de group_vars para que cargue variables del vault/inventario
    src_vars = BASE_DIR / "inventory" / "group_vars"
    dst_vars = cache_dir / "group_vars"
    
    if src_vars.exists():
        try:
            # Si no existe ni es link, crear
            if not dst_vars.exists() and not dst_vars.is_symlink():
                dst_vars.symlink_to(src_vars)
            # Si es link pero está roto (exists() -> False), recrear
            elif dst_vars.is_symlink() and not dst_vars.exists():
                dst_vars.unlink()
                dst_vars.symlink_to(src_vars)
        except Exception as e:
            logger.warning(f"No se pudo configurar symlink de group_vars: {e}")
            
    return cache_dir


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


def _build_dynamic_inventory(
    hostname: str, 
    resolved_ip: Optional[str] = None,
    vault_vars: Optional[Dict[str, str]] = None
) -> str:
    """
    Construye un inventario dinámico en formato INI para un host.
    
    Este inventario permite conectarse a cualquier hostname sin
    necesidad de tenerlo en el archivo hosts.ini estático.
    
    Si resolved_ip está disponible, usa ansible_host para dirigir
    la conexión a esa IP en lugar de depender del DNS local.
    
    Args:
        hostname: El hostname o IP del equipo
        resolved_ip: IP resuelta (opcional, para evitar problemas DNS)
        vault_vars: Variables del vault descifradas (opcional)
        
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
    
    # Usar variables del vault si están disponibles, sino usar referencias {{ }} 
    # para que Ansible las cargue desde group_vars/all/vault.yml cuando se proporcione --vault-password-file
    vault_vars = vault_vars or {}
    #region agent log
    log_path = "/home/korg/Scripts-Laburo/automation/ansible/.cursor/debug.log"
    try:
        with open(log_path, "a") as f:
            import json
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "cli/ansible_runner.py:357", "message": "Construyendo inventario dinámico", "data": {"has_vault_vars": bool(vault_vars), "vault_keys": list(vault_vars.keys()) if vault_vars else [], "has_user": "vault_ansible_user" in vault_vars, "has_password": "vault_ansible_password" in vault_vars}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except: pass
    #endregion
    
    has_user = "vault_ansible_user" in vault_vars
    has_password = "vault_ansible_password" in vault_vars
    
    for key, default_value in DEFAULT_WINRM_VARS.items():
        # Para ansible_user y ansible_password:
        # 1. Si tenemos valores del vault descifrados, usar los valores directamente
        # 2. Si no, usar referencias {{ }} para que Ansible las cargue desde group_vars/all/vault.yml
        if key == "ansible_user":
            if has_user:
                lines.append(f"ansible_user={vault_vars['vault_ansible_user']}")
            else:
                # Usar referencia para que Ansible la cargue del vault
                lines.append(f"ansible_user={default_value}")
        elif key == "ansible_password":
            if has_password:
                lines.append(f"ansible_password={vault_vars['vault_ansible_password']}")
            else:
                # Usar referencia para que Ansible la cargue del vault
                lines.append(f"ansible_password={default_value}")
        else:
            # Para las demás variables, siempre agregar
            lines.append(f"{key}={default_value}")
    
    inventory_content = "\n".join(lines)
    #region agent log
    try:
        with open(log_path, "a") as f:
            import json
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "cli/ansible_runner.py:338", "message": "Inventario dinámico generado", "data": {"content": inventory_content}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except: pass
    #endregion
    return inventory_content


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

    # Descifrar variables del vault si hay password
    vault_vars = {}
    if vault_password:
        vault_vars = _decrypt_vault_vars(vault_password)

    # PowerShell para obtener Snapshot rápido
    ps_script = (
        "$user = (Get-CimInstance Win32_ComputerSystem).UserName; "
        "$os = (Get-CimInstance Win32_OperatingSystem).Caption; "
        "$disk = Get-CimInstance Win32_LogicalDisk -Filter \\\"DeviceID='C:'\\\"; "
        "$free = [math]::round($disk.FreeSpace / 1GB, 1); "
        "$total = [math]::round($disk.Size / 1GB, 1); "
        "@{ user=$user; os=$os; disk_free=$free; disk_total=$total } | ConvertTo-Json"
    )

    inventory_content = _build_dynamic_inventory(hostname, vault_vars=vault_vars)
    # Crear inventario en inventory/ para que Ansible encuentre group_vars/
    inventory_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.ini', dir=str(BASE_DIR / "inventory"), delete=False
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
    
    # Descifrar variables del vault si hay password
    vault_vars = {}
    if vault_password:
        vault_vars = _decrypt_vault_vars(vault_password)
    
    # Crear inventario dinámico temporal en inventory/
    inventory_content = _build_dynamic_inventory(hostname, vault_vars=vault_vars)
    inventory_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.ini', dir=str(BASE_DIR / "inventory"), delete=False
    )
    inventory_file.write(inventory_content)
    inventory_file.close()
    
    cmd = [
        "ansible",
        "-i", inventory_file.name,
        hostname,
        "-m", "win_ping"
    ]
    
    # Manejo de Vault
    vault_file = None
    if vault_password:
        vault_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        vault_file.write(vault_password)
        vault_file.close()
        cmd.extend(["--vault-password-file", vault_file.name])
    
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
    #region agent log
    import json
    log_path = "/home/korg/Scripts-Laburo/automation/ansible/.cursor/debug.log"
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "cli/ansible_runner.py:458", "message": "ejecutar_playbook INICIO", "data": {"hostname": hostname, "playbook_path": playbook_path, "has_vault": vault_password is not None, "has_extra_vars": bool(extra_vars), "show_progress": show_progress, "interactive": interactive}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except: pass
    #endregion
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
        #region agent log
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "F", "location": "cli/ansible_runner.py:480", "message": "Hostname inválido", "data": {"hostname": hostname}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except: pass
        #endregion
        return ExecutionResult(False, None, "", "Hostname inválido", 1)
    
    full_playbook_path = BASE_DIR / "playbooks" / playbook_path
    if not full_playbook_path.exists():
        #region agent log
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "cli/ansible_runner.py:485", "message": "Playbook no encontrado", "data": {"full_path": str(full_playbook_path), "playbook_path": playbook_path}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except: pass
        #endregion
        logger.error(f"Playbook no encontrado: {full_playbook_path}")
        return ExecutionResult(False, None, "", f"Playbook no encontrado: {playbook_path}", 1)

    # Configurar entorno
    env = os.environ.copy()
    env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    if not interactive:
        env["ANSIBLE_STDOUT_CALLBACK"] = "json"
    
    # Asegurar que group_vars esté disponible para el inventario temporal
    # Esto permite que Ansible cargue las variables del vault automáticamente
    inventory_dir = BASE_DIR / "inventory"
    
    # Descifrar variables del vault si hay password
    vault_vars = {}
    if vault_password:
        vault_vars = _decrypt_vault_vars(vault_password)
        #region agent log
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "cli/ansible_runner.py:524", "message": "Vault variables descifradas", "data": {"has_user": "vault_ansible_user" in vault_vars, "has_password": "vault_ansible_password" in vault_vars, "keys": list(vault_vars.keys())}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except: pass
        #endregion
    
    # Crear inventario dinámico temporal en inventory/ (para que Ansible encuentre group_vars/)
    inventory_content = _build_dynamic_inventory(hostname, vault_vars=vault_vars)
    inventory_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.ini', dir=str(BASE_DIR / "inventory"), delete=False
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

        # Modo normal con progreso (simplificado para evitar múltiples mensajes)
        if show_progress:
            # Mostrar mensaje simple una sola vez
            console.print(f"[cyan]🔄 Ejecutando {playbook_path} en {hostname}...[/cyan]")
            result_proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=1200, cwd=str(BASE_DIR))
            # Limpiar la línea anterior
            console.print(f"[dim]✓ Completado[/dim]")
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

        result_obj = ExecutionResult(
            success=result_proc.returncode == 0,
            data=json_data,
            stdout=result_proc.stdout,
            stderr=result_proc.stderr,
            returncode=result_proc.returncode,
            duration=duration
        )
        #region agent log
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "cli/ansible_runner.py:584", "message": "ejecutar_playbook RESULTADO", "data": {"success": result_obj.success, "returncode": result_obj.returncode, "has_stderr": bool(result_obj.stderr), "stderr_preview": result_obj.stderr[:200] if result_obj.stderr else None, "stdout_preview": result_obj.stdout[:200] if result_obj.stdout else None}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except: pass
        #endregion
        return result_obj

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.error(f"Timeout en playbook: {playbook_path}")
        #region agent log
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "cli/ansible_runner.py:587", "message": "Timeout en ejecutar_playbook", "data": {"duration": duration}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except: pass
        #endregion
        return ExecutionResult(False, None, "", "Timeout de ejecución (20 min)", 1, duration)
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error inesperado ejecutando playbook: {e}")
        #region agent log
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "cli/ansible_runner.py:593", "message": "Excepción en ejecutar_playbook", "data": {"error_type": type(e).__name__, "error_msg": str(e)}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except: pass
        #endregion
        return ExecutionResult(False, None, "", str(e), 1, duration)
    finally:
        # Limpiar archivos temporales
        if os.path.exists(inventory_file.name):
            os.unlink(inventory_file.name)
        if vault_file and os.path.exists(vault_file.name):
            os.unlink(vault_file.name)


def ejecutar_playbook_nueva_ventana(
    hostname: str,
    playbook_path: str,
    vault_password: Optional[str] = None,
    extra_vars: Optional[Dict[str, str]] = None
) -> ExecutionResult:
    """
    Ejecuta un playbook en una nueva ventana de terminal para permitir interacción.
    
    Abre una nueva terminal y ejecuta el playbook en modo interactivo.
    Funciona en Linux/WSL detectando el entorno de escritorio disponible.
    
    Args:
        hostname: Hostname del equipo
        playbook_path: Ruta al playbook relativa a playbooks/
        vault_password: Password del vault (opcional)
        extra_vars: Variables extra para el playbook
        
    Returns:
        ExecutionResult: Resultado de la ejecución (exitoso inmediatamente, la ventana sigue abierta)
    """
    full_playbook_path = BASE_DIR / "playbooks" / playbook_path
    if not full_playbook_path.exists():
        logger.error(f"Playbook no encontrado: {full_playbook_path}")
        return ExecutionResult(False, None, "", f"Playbook no encontrado: {playbook_path}", 1)
    
    # Descifrar variables del vault si hay password
    vault_vars = {}
    if vault_password:
        vault_vars = _decrypt_vault_vars(vault_password)
    
    # Crear inventario dinámico temporal
    inventory_content = _build_dynamic_inventory(hostname, vault_vars=vault_vars)
    inventory_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.ini', dir=str(BASE_DIR / "inventory"), delete=False
    )
    inventory_file.write(inventory_content)
    inventory_file.close()
    
    # Construir comando base
    cmd = [
        "ansible-playbook",
        "-i", inventory_file.name,
        str(full_playbook_path),
        "--extra-vars", f"target_host={hostname}"
    ]
    
    # Agregar variables extra
    if extra_vars:
        for key, value in extra_vars.items():
            # Escapar correctamente los valores para evitar problemas con caracteres especiales
            escaped_value = json.dumps(str(value))  # Usar JSON para escapar correctamente
            cmd.extend(["--extra-vars", f"{key}={escaped_value}"])
    
    # Manejo de Vault
    if vault_password:
        vault_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        vault_file.write(vault_password)
        vault_file.close()
        cmd.extend(["--vault-password-file", vault_file.name])
    
    # Detectar entorno de escritorio y construir comando para nueva ventana
    display_env = os.environ.get("DISPLAY")
    wsl_distro = os.environ.get("WSL_DISTRO_NAME")
    
    terminal_cmd = []
    
    # Detectar si estamos en WSL de forma segura
    is_wsl = False
    try:
        if hasattr(os, 'uname'):
            # Linux/WSL
            uname_info = os.uname()
            is_wsl = "microsoft" in uname_info.release.lower() if hasattr(uname_info, 'release') else False
        elif platform.system() == "Linux":
            # Intentar detectar WSL de otra forma
            try:
                with open("/proc/version", "r") as f:
                    version_info = f.read().lower()
                    is_wsl = "microsoft" in version_info or "wsl" in version_info
            except:
                pass
    except:
        pass
    
    if wsl_distro or is_wsl:
        # WSL - usar wsl.exe para abrir terminal de Windows
        # O intentar con terminales de Linux si hay DISPLAY
        if display_env:
            # Hay X11, usar terminal de Linux
            if shutil.which("gnome-terminal"):
                terminal_cmd = [
                    "gnome-terminal", "--",
                    "bash", "-c", f"cd {BASE_DIR} && {' '.join(cmd)}; echo ''; echo 'Presiona Enter para cerrar...'; read"
                ]
            elif shutil.which("xterm"):
                terminal_cmd = [
                    "xterm", "-e", "bash", "-c",
                    f"cd {BASE_DIR} && {' '.join(cmd)}; echo ''; echo 'Presiona Enter para cerrar...'; read"
                ]
            elif shutil.which("konsole"):
                terminal_cmd = [
                    "konsole", "-e", "bash", "-c",
                    f"cd {BASE_DIR} && {' '.join(cmd)}; echo ''; echo 'Presiona Enter para cerrar...'; read"
                ]
            else:
                # Fallback: usar tmux o screen si están disponibles
                logger.warning("No se encontró terminal gráfica, ejecutando en modo normal")
                return ejecutar_playbook(hostname, playbook_path, vault_password, extra_vars, show_progress=True, interactive=True)
        else:
            # Sin DISPLAY, intentar usar cmd.exe de Windows via wsl.exe
            # Convertir comando a formato Windows
            cmd_str = " ".join([f'"{c}"' if " " in c else c for c in cmd])
            terminal_cmd = [
                "wsl.exe", "--", "bash", "-c",
                f"cd {BASE_DIR} && {cmd_str}; echo ''; echo 'Presiona Enter para cerrar...'; read"
            ]
    else:
        # Linux nativo
        if shutil.which("gnome-terminal"):
            terminal_cmd = [
                "gnome-terminal", "--",
                "bash", "-c", f"cd {BASE_DIR} && {' '.join(cmd)}; echo ''; echo 'Presiona Enter para cerrar...'; read"
            ]
        elif shutil.which("xterm"):
            terminal_cmd = [
                "xterm", "-e", "bash", "-c",
                f"cd {BASE_DIR} && {' '.join(cmd)}; echo ''; echo 'Presiona Enter para cerrar...'; read"
            ]
        elif shutil.which("konsole"):
            terminal_cmd = [
                "konsole", "-e", "bash", "-c",
                f"cd {BASE_DIR} && {' '.join(cmd)}; echo ''; echo 'Presiona Enter para cerrar...'; read"
            ]
        else:
            logger.warning("No se encontró terminal gráfica, ejecutando en modo normal")
            return ejecutar_playbook(hostname, playbook_path, vault_password, extra_vars, show_progress=True, interactive=True)
    
    try:
        # Ejecutar en nueva ventana (no bloquear)
        subprocess.Popen(
            terminal_cmd,
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        # Retornar inmediatamente (la ventana sigue abierta)
        return ExecutionResult(
            success=True,
            data=None,
            stdout="Ventana de consola abierta",
            stderr="",
            returncode=0
        )
    except Exception as e:
        logger.error(f"Error abriendo nueva ventana: {e}")
        # Fallback: ejecutar en modo interactivo normal
        console.print(f"[yellow]⚠ No se pudo abrir nueva ventana, ejecutando en modo normal...[/yellow]")
        return ejecutar_playbook(hostname, playbook_path, vault_password, extra_vars, show_progress=True, interactive=True)
    finally:
        # Nota: No eliminamos inventory_file ni vault_file aquí porque la nueva ventana los necesita
        # Se limpiarán cuando termine la ejecución en la nueva ventana
        pass


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
