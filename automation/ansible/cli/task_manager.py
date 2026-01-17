# -*- coding: utf-8 -*-
"""
cli/task_manager.py
===================
Gestor de tareas simultáneas con estado centralizado usando funciones.
"""

import threading
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

from .models import ExecutionResult


@dataclass
class TaskStatus:
    """Estado de una tarea activa"""
    task_id: str
    task_name: str
    target: str  # Hostname o targets múltiples
    playbook: str
    status: str  # RUNNING, SUCCESS, FAILED, CANCELLED
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    error: Optional[str] = None
    result: Optional[ExecutionResult] = None


# Estado global del módulo
_tasks: Dict[str, TaskStatus] = {}
_lock = threading.Lock()


def add_task(
    task_id: str,
    task_name: str,
    target: str,
    playbook: str
) -> None:
    """
    Agregar una nueva tarea al tracking.
    
    Args:
        task_id: ID único de la tarea
        task_name: Nombre de la tarea
        target: Hostname o targets múltiples
        playbook: Ruta del playbook
    """
    with _lock:
        _tasks[task_id] = TaskStatus(
            task_id=task_id,
            task_name=task_name,
            target=target,
            playbook=playbook,
            status="RUNNING",
            start_time=datetime.now()
        )


def update_task(
    task_id: str,
    status: str,
    result: Optional[ExecutionResult] = None,
    error: Optional[str] = None
) -> None:
    """
    Actualizar estado de una tarea.
    
    Args:
        task_id: ID de la tarea
        status: Nuevo estado (RUNNING, SUCCESS, FAILED, CANCELLED)
        result: Resultado de la ejecución
        error: Mensaje de error si falló
    """
    with _lock:
        if task_id in _tasks:
            task = _tasks[task_id]
            task.status = status
            task.end_time = datetime.now()
            if task.start_time:
                task.duration = (task.end_time - task.start_time).total_seconds()
            if result:
                task.result = result
            if error:
                task.error = error


def get_active_tasks() -> List[TaskStatus]:
    """
    Obtener todas las tareas activas (RUNNING).
    
    Returns:
        Lista de tareas con estado RUNNING
    """
    with _lock:
        return [
            task for task in _tasks.values()
            if task.status == "RUNNING"
        ]


def get_all_tasks() -> List[TaskStatus]:
    """
    Obtener todas las tareas.
    
    Returns:
        Lista de todas las tareas
    """
    with _lock:
        return list(_tasks.values())


def get_task(task_id: str) -> Optional[TaskStatus]:
    """
    Obtener una tarea por ID.
    
    Args:
        task_id: ID de la tarea
        
    Returns:
        TaskStatus o None si no existe
    """
    with _lock:
        return _tasks.get(task_id)


def get_summary() -> Dict[str, int]:
    """
    Obtener resumen de tareas por estado.
    
    Returns:
        Diccionario con conteo por estado
    """
    with _lock:
        summary = {"RUNNING": 0, "SUCCESS": 0, "FAILED": 0, "CANCELLED": 0}
        for task in _tasks.values():
            summary[task.status] = summary.get(task.status, 0) + 1
        return summary


def clear_completed() -> None:
    """Limpiar tareas completadas (SUCCESS, FAILED, CANCELLED)."""
    global _tasks
    with _lock:
        _tasks = {
            task_id: task
            for task_id, task in _tasks.items()
            if task.status == "RUNNING"
        }
