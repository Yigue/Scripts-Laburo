# -*- coding: utf-8 -*-
"""
infrastructure/logging/debug_logger.py
=======================================
Logger centralizado para logs de debug del agente.

Reemplaza las regiones `#region agent log` dispersas en el código.
"""

import json
import time
import sys
from pathlib import Path
from typing import Optional, Dict, Any


class DebugLogger:
    """Logger centralizado para debug del agente."""
    
    def __init__(self, log_path: Optional[Path] = None):
        """
        Inicializa el logger.
        
        Args:
            log_path: Ruta al archivo de log. Si es None, usa .cursor/debug.log
        """
        if log_path is None:
            # Buscar directorio .cursor relativo al proyecto
            # Si estamos en un .exe, usar el directorio del ejecutable
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent.absolute()
            else:
                base_dir = Path(__file__).parent.parent.parent.parent.absolute()
            cursor_dir = base_dir / ".cursor"
            cursor_dir.mkdir(exist_ok=True)
            log_path = cursor_dir / "debug.log"
        
        self.log_path = log_path
    
    def log(
        self,
        location: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        session_id: str = "debug-session",
        run_id: str = "run1",
        hypothesis_id: str = "B"
    ) -> None:
        """
        Escribe un log de debug.
        
        Args:
            location: Ubicación en el código (ej: "cli/menus.py:116")
            message: Mensaje descriptivo
            data: Datos adicionales opcionales
            session_id: ID de sesión
            run_id: ID de ejecución
            hypothesis_id: ID de hipótesis
        """
        try:
            log_entry = {
                "sessionId": session_id,
                "runId": run_id,
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data or {},
                "timestamp": int(time.time() * 1000)
            }
            
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception:
            # Silenciar errores de logging para no interrumpir la ejecución
            pass
    
    def log_function_entry(
        self,
        func_name: str,
        file_path: str,
        line_number: int,
        params: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log de entrada a una función.
        
        Args:
            func_name: Nombre de la función
            file_path: Ruta relativa del archivo
            line_number: Número de línea
            params: Parámetros de la función
        """
        location = f"{file_path}:{line_number}"
        message = f"{func_name} INICIO"
        self.log(location, message, params)
    
    def log_function_result(
        self,
        func_name: str,
        file_path: str,
        line_number: int,
        success: bool,
        result_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log de resultado de una función.
        
        Args:
            func_name: Nombre de la función
            file_path: Ruta relativa del archivo
            line_number: Número de línea
            success: Si la ejecución fue exitosa
            result_data: Datos del resultado
        """
        location = f"{file_path}:{line_number}"
        message = f"{func_name} RESULTADO" if success else f"{func_name} ERROR"
        data = {"success": success}
        if result_data:
            data.update(result_data)
        self.log(location, message, data)


# Instancia global del logger
debug_logger = DebugLogger()
