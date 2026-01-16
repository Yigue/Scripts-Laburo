# -*- coding: utf-8 -*-
"""
cli/history.py
==============
Gestión del historial de ejecuciones de la sesión.
"""

from typing import List
from datetime import datetime
from .models import ExecutionStats, ExecutionResult

class SessionHistory:
    def __init__(self):
        self.entries: List[ExecutionStats] = []

    def add_entry(self, hostname: str, task_name: str, result: ExecutionResult):
        """Agrega una nueva ejecución al historial"""
        stats = ExecutionStats(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            hostname=hostname,
            task_name=task_name,
            success=result.success,
            duration=result.duration
        )
        self.entries.append(stats)

    def get_entries(self) -> List[ExecutionStats]:
        return self.entries

# Instancia global para la sesión
session_history = SessionHistory()
