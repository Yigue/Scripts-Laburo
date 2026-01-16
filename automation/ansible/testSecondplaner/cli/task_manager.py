# -*- coding: utf-8 -*-
"""
cli/task_manager.py
===================
Gestor de tareas simultáneas con estado centralizado.
Wrapper sobre BackgroundEngine con tracking mejorado.
"""

import threading
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

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


class TaskManager:
    """Gestor singleton de tareas simultáneas"""
    
    _instance: Optional['TaskManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.tasks: Dict[str, TaskStatus] = {}
        self._lock = threading.Lock()
    
    def add_task(
        self,
        task_id: str,
        task_name: str,
        target: str,
        playbook: str
    ) -> None:
        """Agregar una nueva tarea al tracking"""
        with self._lock:
            self.tasks[task_id] = TaskStatus(
                task_id=task_id,
                task_name=task_name,
                target=target,
                playbook=playbook,
                status="RUNNING",
                start_time=datetime.now()
            )
    
    def update_task(
        self,
        task_id: str,
        status: str,
        result: Optional[ExecutionResult] = None,
        error: Optional[str] = None
    ) -> None:
        """Actualizar estado de una tarea"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = status
                task.end_time = datetime.now()
                if task.start_time:
                    task.duration = (task.end_time - task.start_time).total_seconds()
                if result:
                    task.result = result
                if error:
                    task.error = error
    
    def get_active_tasks(self) -> List[TaskStatus]:
        """Obtener todas las tareas activas (RUNNING)"""
        with self._lock:
            return [
                task for task in self.tasks.values()
                if task.status == "RUNNING"
            ]
    
    def get_all_tasks(self) -> List[TaskStatus]:
        """Obtener todas las tareas"""
        with self._lock:
            return list(self.tasks.values())
    
    def get_task(self, task_id: str) -> Optional[TaskStatus]:
        """Obtener una tarea por ID"""
        with self._lock:
            return self.tasks.get(task_id)
    
    def get_summary(self) -> Dict[str, int]:
        """Obtener resumen de tareas por estado"""
        with self._lock:
            summary = {"RUNNING": 0, "SUCCESS": 0, "FAILED": 0, "CANCELLED": 0}
            for task in self.tasks.values():
                summary[task.status] = summary.get(task.status, 0) + 1
            return summary
    
    def clear_completed(self) -> None:
        """Limpiar tareas completadas (SUCCESS, FAILED, CANCELLED)"""
        with self._lock:
            self.tasks = {
                task_id: task
                for task_id, task in self.tasks.items()
                if task.status == "RUNNING"
            }


# Instancia singleton
task_manager = TaskManager()
