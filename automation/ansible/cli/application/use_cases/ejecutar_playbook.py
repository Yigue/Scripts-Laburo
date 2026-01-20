# -*- coding: utf-8 -*-
"""
application/use_cases/ejecutar_playbook.py
==========================================
Caso de uso: Ejecutar playbook.

Orquesta la validación, construcción de inventario y ejecución de un playbook de Ansible.
"""

from typing import Optional, Dict

from ...domain.models import ExecutionResult
from ...domain.services.validation_service import validate_hostname
from ...infrastructure.ansible.playbook_executor import execute_playbook


def ejecutar_playbook_use_case(
    hostname: str,
    playbook_path: str,
    vault_password: Optional[str] = None,
    extra_vars: Optional[Dict[str, str]] = None,
    show_progress: bool = True,
    interactive: bool = False
) -> ExecutionResult:
    """
    Caso de uso para ejecutar un playbook de Ansible.
    
    Valida el hostname y delega la ejecución al executor de playbooks.
    
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
    # Validar hostname
    if not validate_hostname(hostname):
        return ExecutionResult(False, None, "", "Hostname inválido", 1)
    
    # Delegar ejecución al executor de infrastructure
    return execute_playbook(
        hostname=hostname,
        playbook_path=playbook_path,
        vault_password=vault_password,
        extra_vars=extra_vars,
        show_progress=show_progress,
        interactive=interactive
    )
