# -*- coding: utf-8 -*-
"""
infrastructure/terminal/terminal_detector.py
===========================================
Detector de terminales gráficas.

Contiene funciones para detectar y abrir terminales gráficas disponibles
para ejecutar playbooks en nuevas ventanas.
"""

import os
import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List

from ...shared.config import BASE_DIR, logger, console
from ...domain.models import ExecutionResult
from ..ansible.playbook_executor import execute_playbook
from ..ansible.vault_manager import decrypt_vault
from ..ansible.inventory_builder import build_dynamic_inventory


def detect_terminal() -> Optional[str]:
    """
    Detecta qué terminal gráfica está disponible.
    
    Returns:
        Nombre del comando del terminal disponible o None
    """
    # Prioridad: gnome-terminal > xterm > konsole
    terminals = ["gnome-terminal", "xterm", "konsole"]
    for term in terminals:
        if shutil.which(term):
            return term
    return None


def is_wsl() -> bool:
    """
    Detecta si estamos ejecutando en WSL.
    
    Returns:
        True si está en WSL, False en caso contrario
    """
    try:
        if hasattr(os, 'uname'):
            uname_info = os.uname()
            if hasattr(uname_info, 'release'):
                return "microsoft" in uname_info.release.lower()
        elif platform.system() == "Linux":
            try:
                with open("/proc/version", "r") as f:
                    version_info = f.read().lower()
                    return "microsoft" in version_info or "wsl" in version_info
            except:
                pass
    except:
        pass
    return False


def build_terminal_command(base_cmd: List[str], base_dir: Path) -> Optional[List[str]]:
    """
    Construye el comando para abrir una terminal con el comando base.
    
    Args:
        base_cmd: Comando base a ejecutar (ej: ["ansible-playbook", ...])
        base_dir: Directorio base del proyecto
        
    Returns:
        Comando completo para abrir terminal o None si no hay terminal disponible
    """
    display_env = os.environ.get("DISPLAY")
    wsl_distro = os.environ.get("WSL_DISTRO_NAME")
    is_wsl_env = is_wsl() or bool(wsl_distro)
    
    terminal = detect_terminal()
    cmd_str = " ".join([f'"{c}"' if " " in c else c for c in base_cmd])
    terminal_cmd_base = f"cd {base_dir} && {cmd_str}; echo ''; echo 'Presiona Enter para cerrar...'; read"
    
    if is_wsl_env:
        if display_env:
            # Hay X11, usar terminal de Linux
            if terminal == "gnome-terminal":
                return ["gnome-terminal", "--", "bash", "-c", terminal_cmd_base]
            elif terminal == "xterm":
                return ["xterm", "-e", "bash", "-c", terminal_cmd_base]
            elif terminal == "konsole":
                return ["konsole", "-e", "bash", "-c", terminal_cmd_base]
        else:
            # Sin DISPLAY, intentar usar cmd.exe de Windows via wsl.exe
            return ["wsl.exe", "--", "bash", "-c", terminal_cmd_base]
    else:
        # Linux nativo
        if terminal == "gnome-terminal":
            return ["gnome-terminal", "--", "bash", "-c", terminal_cmd_base]
        elif terminal == "xterm":
            return ["xterm", "-e", "bash", "-c", terminal_cmd_base]
        elif terminal == "konsole":
            return ["konsole", "-e", "bash", "-c", terminal_cmd_base]
    
    return None


def execute_playbook_in_new_window(
    hostname: str,
    playbook_path: str,
    vault_password: Optional[str] = None,
    extra_vars: Optional[dict] = None
) -> ExecutionResult:
    """
    Ejecuta un playbook en una nueva ventana de terminal para permitir interacción.
    
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
        vault_vars = decrypt_vault(vault_password)
    
    # Crear inventario dinámico temporal
    inventory_content = build_dynamic_inventory(hostname, vault_vars=vault_vars)
    import tempfile
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
            escaped_value = json.dumps(str(value))
            cmd.extend(["--extra-vars", f"{key}={escaped_value}"])
    
    # Manejo de Vault
    vault_file = None
    if vault_password:
        vault_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        vault_file.write(vault_password)
        vault_file.close()
        cmd.extend(["--vault-password-file", vault_file.name])
    
    # Construir comando de terminal
    terminal_cmd = build_terminal_command(cmd, BASE_DIR)
    
    if not terminal_cmd:
        logger.warning("No se encontró terminal gráfica, ejecutando en modo normal")
        return execute_playbook(hostname, playbook_path, vault_password, extra_vars, show_progress=True, interactive=True)
    
    try:
        # Ejecutar en nueva ventana (no bloquear)
        subprocess.Popen(
            terminal_cmd,
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return ExecutionResult(
            success=True,
            data=None,
            stdout="Ventana de consola abierta",
            stderr="",
            returncode=0
        )
    except Exception as e:
        logger.error(f"Error abriendo nueva ventana: {e}")
        console.print(f"[yellow]⚠ No se pudo abrir nueva ventana, ejecutando en modo normal...[/yellow]")
        return execute_playbook(hostname, playbook_path, vault_password, extra_vars, show_progress=True, interactive=True)
