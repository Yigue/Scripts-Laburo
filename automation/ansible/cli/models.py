# -*- coding: utf-8 -*-
"""
cli/models.py
=============
Modelos de datos (dataclasses).

Contiene:
- MenuOption: Una opción de menú
- MenuCategory: Una categoría de menú
- ExecutionResult: Resultado de ejecución de playbook
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Any


@dataclass
class MenuOption:
    """
    Opción de menú.
    
    Attributes:
        key: Tecla de acceso rápido (ej: "H1")
        label: Etiqueta visible (ej: "Mostrar especificaciones")
        playbook: Ruta relativa al playbook (ej: "hardware/specs.yml")
        description: Descripción detallada
        requires_input: Si necesita input adicional del usuario
        input_prompt: Mensaje para solicitar input
        input_var_name: Nombre de la variable para pasar a Ansible
    """
    key: str
    label: str
    playbook: str
    description: str = ""
    requires_input: bool = False
    input_prompt: str = ""
    input_var_name: str = ""


@dataclass
class MenuCategory:
    """
    Categoría de menú.
    
    Attributes:
        key: Tecla de acceso rápido (ej: "H")
        name: Nombre de la categoría (ej: "Hardware y Sistema")
        icon: Emoji para la categoría
        options: Lista de opciones en esta categoría
    """
    key: str
    name: str
    icon: str
    options: List[MenuOption]


@dataclass
class HostSnapshot:
    """Información rápida del host"""
    hostname: str
    user: str
    os: str
    disk_free: float
    disk_total: float

@dataclass
class ExecutionResult:
    """
    Resultado de ejecución de playbook.
    
    Attributes:
        success: True si la ejecución fue exitosa
        data: Datos JSON parseados (si hay)
        stdout: Salida estándar completa
        stderr: Salida de error
        returncode: Código de retorno del proceso
        duration: Tiempo de ejecución en segundos
    """
    success: bool
    data: Optional[Dict[str, Any]]
    stdout: str
    stderr: str
    returncode: int
    duration: float = 0.0

@dataclass
class ExecutionStats:
    """Estadística de una ejecución para el historial"""
    timestamp: str
    hostname: str
    task_name: str
    success: bool
    duration: float
