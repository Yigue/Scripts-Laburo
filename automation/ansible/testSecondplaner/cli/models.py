# -*- coding: utf-8 -*-
"""
cli/models.py
=============
Modelos de datos (dataclasses) mejorados.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from datetime import datetime


@dataclass
class MenuOption:
    """
    Opción de menú mejorada con soporte para ejecución en segundo plano.
    
    Attributes:
        key: Tecla de acceso rápido (ej: "H1", "A2")
        label: Etiqueta visible
        playbook: Ruta relativa al playbook
        description: Descripción detallada
        requires_input: Si necesita input adicional
        input_prompt: Mensaje para solicitar input
        input_var_name: Nombre de la variable para Ansible
        action_type: Tipo de acción (read-only, modify, destructive)
        can_background: Si puede ejecutarse en segundo plano
        can_new_window: Si puede abrirse en nueva ventana
        requires_hostname: Si requiere hostname para ejecutarse
    """
    key: str
    label: str
    playbook: str
    description: str = ""
    requires_input: bool = False
    input_prompt: str = ""
    input_var_name: str = ""
    action_type: str = "read-only"  # read-only, modify, destructive
    can_background: bool = True
    can_new_window: bool = False  # Para consolas interactivas
    requires_hostname: bool = True  # Por defecto requiere hostname


@dataclass
class MenuCategory:
    """
    Categoría de menú con estética mejorada.
    
    Attributes:
        key: Tecla de acceso rápido (ej: "H", "A")
        name: Nombre de la categoría
        icon: Emoji para la categoría
        options: Lista de opciones
        color: Color del tema (cyan, green, yellow, etc.)
    """
    key: str
    name: str
    icon: str
    options: List[MenuOption]
    color: str = "cyan"


@dataclass
class HostSnapshot:
    """Información rápida del host con métricas visuales"""
    hostname: str
    user: str
    os: str
    disk_free: float
    disk_total: float
    last_check: Optional[datetime] = None


@dataclass
class ExecutionResult:
    """
    Resultado de ejecución mejorado con soporte para jobs.
    
    Attributes:
        success: True si fue exitosa
        data: Datos JSON parseados
        stdout: Salida estándar
        stderr: Salida de error
        returncode: Código de retorno
        duration: Tiempo de ejecución
        job_id: ID del job si se ejecutó en segundo plano
        is_background: Si está ejecutándose en segundo plano
    """
    success: bool
    data: Optional[Dict[str, Any]]
    stdout: str
    stderr: str
    returncode: int
    duration: float = 0.0
    job_id: Optional[str] = None
    is_background: bool = False


@dataclass
class ExecutionStats:
    """Estadística de ejecución para historial y dashboard"""
    timestamp: str
    hostname: str
    task_name: str
    success: bool
    duration: float
    job_id: Optional[str] = None
