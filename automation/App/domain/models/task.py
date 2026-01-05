"""
Modelo de Task - Representación de una tarea a ejecutar
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class TaskStatus(Enum):
    """Estados posibles de una tarea"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Representación de una tarea a ejecutar en un host"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hostname: str = ""
    operation: str = ""
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"Task({self.id[:8]}, {self.hostname}, {self.operation}, {self.status.value})"
    
    def start(self):
        """Marca la tarea como iniciada"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
    
    def complete(self, result: Any = None):
        """Marca la tarea como completada"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
    
    def fail(self, error: str):
        """Marca la tarea como fallida"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
    
    def cancel(self):
        """Marca la tarea como cancelada"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
    
    @property
    def duration(self) -> Optional[float]:
        """Retorna duración en segundos si la tarea finalizó"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_finished(self) -> bool:
        """Verifica si la tarea terminó (éxito o fallo)"""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)

