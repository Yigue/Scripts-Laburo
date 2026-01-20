# -*- coding: utf-8 -*-
"""
application/use_cases/ejecutar_opcion.py
========================================
Caso de uso: Ejecutar opción del menú.

Orquesta la ejecución de una opción del menú: validación, confirmación,
selección de modo de ejecución, y presentación de resultados.
"""

import uuid
import threading
from typing import Optional, Dict, List

import questionary

from ...domain.models import MenuOption, ExecutionResult
from ...shared.config import console, CUSTOM_STYLE, logger
from ...infrastructure.logging.debug_logger import debug_logger
from ..validators.script_validator import validate_powershell_script
from .ejecutar_playbook import ejecutar_playbook_use_case


def ejecutar_opcion_use_case(
    opcion: MenuOption,
    targets: List[str],
    vault_password: Optional[str] = None,
    extra_vars: Optional[Dict[str, str]] = None,
    execution_mode: str = "normal"
) -> List[Optional[ExecutionResult]]:
    """
    Caso de uso para ejecutar una opción del menú.
    
    Args:
        opcion: La opción de menú a ejecutar
        targets: Lista de hostnames donde ejecutar
        vault_password: Password del vault (opcional)
        extra_vars: Variables extra para el playbook
        execution_mode: Modo de ejecución ("normal", "background", "new_window")
        
    Returns:
        Lista de resultados (None para background)
    """
    from ...infrastructure.terminal.terminal_detector import execute_playbook_in_new_window
    from cli.task_manager import add_task as task_add_task, update_task as task_update_task
    from cli.history import add_entry as history_add_entry
    
    results = []
    
    for target_host in targets:
        task_id = str(uuid.uuid4())[:8]
        
        # Registrar tarea
        task_add_task(
            task_id=task_id,
            task_name=opcion.label,
            target=target_host if target_host else "N/A",
            playbook=opcion.playbook
        )
        
        if execution_mode == "new_window":
            if target_host:
                result = execute_playbook_in_new_window(
                    hostname=target_host,
                    playbook_path=opcion.playbook,
                    vault_password=vault_password,
                    extra_vars=extra_vars
                )
                results.append(result)
        elif execution_mode == "background":
            # Ejecutar en background (thread)
            def execute_and_track():
                debug_logger.log(
                    "application/use_cases/ejecutar_opcion.py:59",
                    "Thread background INICIO",
                    {"target_host": target_host, "playbook": opcion.playbook},
                    hypothesis_id="B"
                )
                try:
                    hostname_to_use = target_host if target_host else "localhost"
                    if not opcion.requires_hostname and not target_host:
                        hostname_to_use = "localhost"
                    
                    result = ejecutar_playbook_use_case(
                        hostname=hostname_to_use,
                        playbook_path=opcion.playbook,
                        vault_password=vault_password,
                        extra_vars=extra_vars,
                        show_progress=False
                    )
                    
                    status = "SUCCESS" if result.success else "FAILED"
                    task_update_task(task_id, status, result, result.stderr if not result.success else None)
                    
                    if target_host:
                        history_add_entry(target_host, opcion.label, result)
                except Exception as e:
                    logger.error(f"Error en thread {task_id}: {e}", exc_info=True)
                    task_update_task(task_id, "FAILED", error=str(e))
            
            thread = threading.Thread(target=execute_and_track, daemon=True)
            thread.start()
            results.append(None)  # Placeholder para background
        else:
            # Ejecución normal
            debug_logger.log(
                "application/use_cases/ejecutar_opcion.py:88",
                "Antes de ejecutar_playbook (normal)",
                {
                    "target_host": target_host,
                    "playbook": opcion.playbook,
                    "has_vault": vault_password is not None,
                    "has_extra_vars": bool(extra_vars),
                    "interactive": opcion.key == "C1"
                },
                hypothesis_id="B"
            )
            
            try:
                hostname_to_use = target_host if target_host else "localhost"
                if not opcion.requires_hostname and not target_host:
                    hostname_to_use = "localhost"
                
                result = ejecutar_playbook_use_case(
                    hostname=hostname_to_use,
                    playbook_path=opcion.playbook,
                    vault_password=vault_password,
                    extra_vars=extra_vars,
                    show_progress=True,
                    interactive=(opcion.key == "C1")
                )
                
                debug_logger.log_function_result(
                    "ejecutar_playbook_use_case",
                    "application/use_cases/ejecutar_opcion.py:111",
                    result.success,
                    {
                        "returncode": result.returncode,
                        "has_stderr": bool(result.stderr)
                    }
                )
                
                status = "SUCCESS" if result.success else "FAILED"
                task_update_task(task_id, status, result, result.stderr if not result.success else None)
                results.append(result)
                
                if target_host:
                    history_add_entry(target_host, opcion.label, result)
            except Exception as e:
                debug_logger.log(
                    "application/use_cases/ejecutar_opcion.py:124",
                    "Error en ejecutar_playbook",
                    {"error_type": type(e).__name__, "error_msg": str(e)},
                    hypothesis_id="B"
                )
                raise
    
    return results


def preparar_extra_vars(opcion: MenuOption, user_input: Optional[str] = None) -> Dict[str, str]:
    """
    Prepara las variables extra para el playbook.
    
    Args:
        opcion: La opción de menú
        user_input: Input adicional del usuario (opcional)
        
    Returns:
        Diccionario con las variables extra
    """
    extra_vars = {}
    
    if opcion.requires_input and user_input:
        # Validar si es script PowerShell
        if opcion.key == "C2" and opcion.input_var_name == "custom_script":
            validated_input = validate_powershell_script(user_input)
            if validated_input is None:
                raise ValueError("Script PowerShell rechazado por seguridad")
            user_input = validated_input
        
        var_name = opcion.input_var_name if opcion.input_var_name else "user_input"
        extra_vars[var_name] = user_input
    
    return extra_vars


def determinar_modo_ejecucion(
    opcion: MenuOption,
    targets: List[str],
    can_new_window: bool = False
) -> str:
    """
    Determina el modo de ejecución basado en la opción y targets.
    
    Args:
        opcion: La opción de menú
        targets: Lista de hostnames
        can_new_window: Si está disponible ejecutar en nueva ventana
        
    Returns:
        Modo de ejecución: "normal", "background", o "new_window"
    """
    # Nueva ventana para consola remota
    if can_new_window and opcion.can_new_window and opcion.key == "C1":
        return "new_window"
    
    # Múltiples targets siempre en background
    if len(targets) > 1:
        return "background"
    
    # Para read-only, preguntar al usuario
    if opcion.can_background and opcion.action_type == "read-only":
        mode_choice = questionary.select(
            "¿Cómo deseas ejecutar esta tarea?",
            choices=[
                "Ejecutar normalmente (ver resultado inmediato)",
                "Ejecutar en segundo plano (continuar trabajando)"
            ],
            style=CUSTOM_STYLE,
            use_shortcuts=True
        ).ask()
        
        if mode_choice and "segundo plano" in mode_choice:
            return "background"
    
    return "normal"
