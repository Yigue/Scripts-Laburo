# -*- coding: utf-8 -*-
"""
cli/history.py
==============
Gestión del historial de ejecuciones de la sesión usando funciones.
"""

from typing import List
from datetime import datetime
from .models import ExecutionStats, ExecutionResult


# Estado global del módulo
_entries: List[ExecutionStats] = []


def add_entry(hostname: str, task_name: str, result: ExecutionResult) -> None:
    """
    Agrega una nueva ejecución al historial.
    
    Args:
        hostname: Hostname del equipo
        task_name: Nombre de la tarea ejecutada
        result: Resultado de la ejecución
    """
    stats = ExecutionStats(
        timestamp=datetime.now().strftime("%H:%M:%S"),
        hostname=hostname,
        task_name=task_name,
        success=result.success,
        duration=result.duration
    )
    _entries.append(stats)


def get_entries() -> List[ExecutionStats]:
    """
    Obtiene todas las entradas del historial.
    
    Returns:
        Lista de estadísticas de ejecuciones
    """
    return _entries.copy()  # Retornar copia para evitar modificación externa


def clear_history() -> None:
    """Limpia el historial de la sesión."""
    global _entries
    _entries.clear()
