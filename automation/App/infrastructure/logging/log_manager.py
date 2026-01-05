"""
LogManager - Sistema de logging estructurado con rotación
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from config import get_config
from domain.interfaces import ILogger


class LogManager(ILogger):
    """
    Gestor de logging con rotación automática
    Implementa ILogger interface
    """
    
    def __init__(self, name: str = "automation", log_dir: Optional[str] = None):
        """
        Inicializa el gestor de logging
        
        Args:
            name: Nombre del logger
            log_dir: Directorio donde guardar logs (usa config si no se especifica)
        """
        self.config = get_config()
        self.logger = logging.getLogger(name)
        
        # Evitar duplicar handlers
        if not self.logger.handlers:
            self._setup_logger(log_dir)
    
    def _setup_logger(self, log_dir: Optional[str] = None):
        """Configura el logger con handlers de archivo y consola"""
        
        # Configurar nivel de log desde config
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Crear directorio de logs si no existe
        if log_dir is None:
            log_dir = self.config.log_dir
        
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Formato de logs
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler de archivo con rotación
        log_file = os.path.join(log_dir, "automation.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.config.log_max_bytes,
            backupCount=self.config.log_backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Handler de consola (solo para WARNING y superiores)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs):
        """Log nivel DEBUG"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log nivel INFO"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log nivel WARNING"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log nivel ERROR"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log nivel CRITICAL"""
        self.logger.critical(message, extra=kwargs)
    
    def log_operation(self, hostname: str, operation: str, success: bool, 
                     duration: float, details: str = ""):
        """
        Log especializado para operaciones remotas
        
        Args:
            hostname: Host donde se ejecutó
            operation: Operación ejecutada
            success: Si fue exitosa
            duration: Duración en segundos
            details: Detalles adicionales
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"Operation: {operation} | Host: {hostname} | Status: {status} | Duration: {duration:.2f}s"
        
        if details:
            message += f" | Details: {details}"
        
        if success:
            self.info(message)
        else:
            self.error(message)
    
    def log_exception(self, message: str, exc: Exception):
        """
        Log de excepción con stack trace
        
        Args:
            message: Mensaje descriptivo
            exc: Excepción capturada
        """
        self.logger.exception(f"{message}: {exc}")


# Instancia global de logger
_logger_instance: Optional[LogManager] = None


def get_logger(name: str = "automation") -> LogManager:
    """
    Obtiene la instancia global del logger (singleton)
    
    Args:
        name: Nombre del logger
        
    Returns:
        LogManager: Instancia del gestor de logging
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = LogManager(name)
    return _logger_instance

