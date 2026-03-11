# -*- coding: utf-8 -*-
"""
infrastructure/ansible/playbook_executor.py
==========================================
Ejecutor de playbooks de Ansible.

Contiene la lógica de bajo nivel para ejecutar playbooks de Ansible.
"""

import os
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict

from ...shared.config import BASE_DIR, logger, console
from ...domain.models import ExecutionResult
from ..ansible.vault_manager import decrypt_vault, load_common_vars
from ..ansible.inventory_builder import build_dynamic_inventory
from ...infrastructure.logging.debug_logger import debug_logger


def execute_playbook(
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
    debug_logger.log_function_entry(
        "execute_playbook",
        "infrastructure/ansible/playbook_executor.py",
        40,
        {
            "hostname": hostname,
            "playbook_path": playbook_path,
            "has_vault": vault_password is not None,
            "has_extra_vars": bool(extra_vars),
            "show_progress": show_progress,
            "interactive": interactive
        }
    )
    
    full_playbook_path = BASE_DIR / "playbooks" / playbook_path
    if not full_playbook_path.exists():
        debug_logger.log(
            "infrastructure/ansible/playbook_executor.py:53",
            "Playbook no encontrado",
            {"full_path": str(full_playbook_path), "playbook_path": playbook_path},
            hypothesis_id="B"
        )
        logger.error(f"Playbook no encontrado: {full_playbook_path}")
        return ExecutionResult(False, None, "", f"Playbook no encontrado: {playbook_path}", 1)

    # Configurar entorno
    env = os.environ.copy()
    env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
    if not interactive:
        env["ANSIBLE_STDOUT_CALLBACK"] = "json"
    
    # Leer contenido del playbook para determinar si usa localhost
    playbook_content = full_playbook_path.read_text()
    uses_localhost = "hosts: localhost" in playbook_content or "'localhost'" in playbook_content or '"localhost"' in playbook_content
    
    # Descifrar variables del vault si hay password
    vault_vars = {}
    if vault_password:
        vault_vars = decrypt_vault(vault_password)
        debug_logger.log(
            "infrastructure/ansible/playbook_executor.py:72",
            "Vault variables descifradas",
            {
                "has_user": "vault_ansible_user" in vault_vars,
                "has_password": "vault_ansible_password" in vault_vars,
                "keys": list(vault_vars.keys())
            },
            hypothesis_id="E"
        )
    
    # Crear inventario dinámico solo si NO usa localhost
    inventory_file = None
    if not uses_localhost:
        inventory_content = build_dynamic_inventory(hostname, vault_vars=vault_vars)
        inventory_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.ini', dir=str(BASE_DIR / "inventory"), delete=False
        )
        inventory_file.write(inventory_content)
        inventory_file.close()
    
    # Construir comando base
    if uses_localhost:
        # Para playbooks que usan localhost, forzar conexión local explícitamente
        cmd = [
            "ansible-playbook",
            "-i", "localhost,",
            "-c", "local",  # Forzar conexión local para evitar SSH
            str(full_playbook_path)
        ]
    else:
        # Para playbooks que se conectan al host, usar inventario dinámico
        cmd = [
            "ansible-playbook",
            "-i", inventory_file.name,
            str(full_playbook_path)
        ]
    
    # Pasar target_host universalmente si existe hostname (solución genérica)
    if hostname and hostname != "localhost":
        cmd.extend(["--extra-vars", f"target_host={hostname}"])
        
        # Para playbooks SCCM que también esperan sccm_device_name
        if "sccm" in playbook_path:
            cmd.extend(["--extra-vars", f"sccm_device_name={hostname}"])
    
    # Agregar variables extra del usuario
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
        
        # Para playbooks localhost, pasar vault vars como extra vars (necesario para delegate_to)
        if uses_localhost and vault_vars:
            for key, value in vault_vars.items():
                cmd.extend(["--extra-vars", f"{key}={value}"])
    
    # Para playbooks localhost, también pasar common vars (sccm_server, domain_controller, etc.)
    if uses_localhost:
        common_vars = load_common_vars()
        for key, value in common_vars.items():
            cmd.extend(["--extra-vars", f"{key}={value}"])

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
            console.print(f"[cyan]🔄 Ejecutando {playbook_path} en {hostname}...[/cyan]")
            result_proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=1200, cwd=str(BASE_DIR))
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
        debug_logger.log_function_result(
            "execute_playbook",
            "infrastructure/ansible/playbook_executor.py",
            166,
            result_obj.success,
            {
                "returncode": result_obj.returncode,
                "has_stderr": bool(result_obj.stderr),
                "stderr_preview": result_obj.stderr[:200] if result_obj.stderr else None,
                "stdout_preview": result_obj.stdout[:200] if result_obj.stdout else None
            }
        )
        return result_obj

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.error(f"Timeout en playbook: {playbook_path}")
        debug_logger.log(
            "infrastructure/ansible/playbook_executor.py:180",
            "Timeout en ejecutar_playbook",
            {"duration": duration},
            hypothesis_id="B"
        )
        return ExecutionResult(False, None, "", "Timeout de ejecución (20 min)", 1, duration)
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Error inesperado ejecutando playbook: {e}")
        debug_logger.log(
            "infrastructure/ansible/playbook_executor.py:188",
            "Excepción en ejecutar_playbook",
            {"error_type": type(e).__name__, "error_msg": str(e)},
            hypothesis_id="B"
        )
        return ExecutionResult(False, None, "", str(e), 1, duration)
    finally:
        # Limpiar archivos temporales
        if inventory_file and os.path.exists(inventory_file.name):
            os.unlink(inventory_file.name)
        if vault_file and os.path.exists(vault_file.name):
            os.unlink(vault_file.name)
