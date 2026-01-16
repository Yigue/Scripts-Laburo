# -*- coding: utf-8 -*-
"""
cli/history.py
==============
Sistema de historial de sesión mejorado.
"""

from datetime import datetime
from typing import List
from dataclasses import dataclass, field

from .models import ExecutionStats, ExecutionResult


@dataclass
class SessionHistory:
    """Historial de la sesión actual"""
    entries: List[ExecutionStats] = field(default_factory=list)
    
    def add_entry(self, hostname: str, task_name: str, result: ExecutionResult):
        """Agregar entrada al historial"""
        entry = ExecutionStats(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            hostname=hostname,
            task_name=task_name,
            success=result.success,
            duration=result.duration,
            job_id=result.job_id
        )
        self.entries.append(entry)
    
    def get_entries(self) -> List[ExecutionStats]:
        """Obtener todas las entradas"""
        return self.entries.copy()
    
    def clear(self):
        """Limpiar historial"""
        self.entries.clear()


# Instancia global del historial
session_history = SessionHistory()
