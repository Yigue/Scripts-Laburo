# -*- coding: utf-8 -*-
"""
domain/services/validation_service.py
====================================
Servicio de validación del dominio.

Contiene funciones de validación de hostnames y verificación de entorno.
"""

import shutil
import sys
from typing import Optional
from rich.panel import Panel

from ...shared.config import BASE_DIR, console, logger


def check_environment() -> None:
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
