# -*- coding: utf-8 -*-
"""
infrastructure/ansible/health_checker.py
========================================
Verificador de salud de hosts.

Contiene funciones para verificar conectividad y obtener información rápida de hosts.
"""

import os
import json
import subprocess
import socket
import tempfile
from typing import Optional

import questionary
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...shared.config import BASE_DIR, logger, console
from ...domain.models import HostSnapshot, ExecutionResult
from ..ansible.vault_manager import decrypt_vault
from ..ansible.inventory_builder import build_dynamic_inventory
from ...domain.services.validation_service import validate_hostname


def check_host_online(hostname: str, vault_password: Optional[str] = None) -> bool:
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
        vault_vars = decrypt_vault(vault_password)
    
    # Crear inventario dinámico temporal en inventory/
    inventory_content = build_dynamic_inventory(hostname, vault_vars=vault_vars)
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
            
            # Si el host es localhost, ofrecer reparación
            my_hostname = socket.gethostname().lower()
            if hostname.lower() in [my_hostname, "localhost", "127.0.0.1"]:
                if questionary.confirm("¿Deseas ver los comandos para reparar WinRM localmente?", default=True).ask():
                    # Importar aquí para evitar dependencia circular
                    from ..ansible.winrm_repair import repair_winrm_local
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
        # Limpiar archivos temporales
        if os.path.exists(inventory_file.name):
            os.unlink(inventory_file.name)
        if vault_file and os.path.exists(vault_file.name):
            os.unlink(vault_file.name)


def get_host_snapshot(hostname: str, vault_password: Optional[str] = None) -> Optional[HostSnapshot]:
    """
    Obtiene información rápida del host (Usuario, OS, Disco).
    
    Se ejecuta como un paso rápido tras verificar que el host está online.
    
    Args:
        hostname: Hostname del equipo
        vault_password: Password del vault (opcional)
        
    Returns:
        HostSnapshot con información del host o None si falla
    """
    env = os.environ.copy()
    env["ANSIBLE_STDOUT_CALLBACK"] = "json"
    env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    if vault_password:
        env["ANSIBLE_VAULT_PASSWORD"] = vault_password

    # Descifrar variables del vault si hay password
    vault_vars = {}
    if vault_password:
        vault_vars = decrypt_vault(vault_password)

    # PowerShell para obtener Snapshot rápido
    ps_script = (
        "$user = (Get-CimInstance Win32_ComputerSystem).UserName; "
        "$os = (Get-CimInstance Win32_OperatingSystem).Caption; "
        "$disk = Get-CimInstance Win32_LogicalDisk -Filter \\\"DeviceID='C:'\\\"; "
        "$free = [math]::round($disk.FreeSpace / 1GB, 1); "
        "$total = [math]::round($disk.Size / 1GB, 1); "
        "@{ user=$user; os=$os; disk_free=$free; disk_total=$total } | ConvertTo-Json"
    )

    inventory_content = build_dynamic_inventory(hostname, vault_vars=vault_vars)
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
