"""
Interfaces abstractas para la aplicación
Define contratos que deben cumplir las implementaciones
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============================================================================
# MODELOS (definiciones forward para type hints)
# ============================================================================
class Host:
    """Representación de un host remoto"""
    hostname: str
    ip: Optional[str]
    is_online: bool


class Task:
    """Representación de una tarea a ejecutar"""
    id: str
    hostname: str
    operation: str
    status: str
    created_at: datetime


class Result:
    """Resultado de una operación"""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    method_used: str
    error: Optional[str]


# ============================================================================
# INTERFACES DE EJECUCIÓN REMOTA
# ============================================================================
class IRemoteExecutor(ABC):
    """
    Interfaz para ejecutores remotos (WinRM, PsExec, Ansible)
    Implementa Strategy Pattern
    """
    
    @abstractmethod
    def execute(self, host: Host, command: str, timeout: int = 120) -> Result:
        """
        Ejecuta un comando en el host remoto
        
        Args:
            host: Host donde ejecutar
            command: Comando a ejecutar
            timeout: Timeout en segundos
            
        Returns:
            Result: Resultado de la ejecución
        """
        pass
    
    @abstractmethod
    def execute_script(self, host: Host, script: str, timeout: int = 120) -> Result:
        """
        Ejecuta un script PowerShell en el host remoto
        
        Args:
            host: Host donde ejecutar
            script: Script PowerShell completo
            timeout: Timeout en segundos
            
        Returns:
            Result: Resultado de la ejecución
        """
        pass
    
    @abstractmethod
    def test_connection(self, host: Host) -> bool:
        """
        Prueba conectividad con el host
        
        Args:
            host: Host a probar
            
        Returns:
            bool: True si la conexión es exitosa
        """
        pass


class ISessionManager(ABC):
    """Interfaz para gestión de sesiones remotas"""
    
    @abstractmethod
    def get_session(self, host: Host):
        """Obtiene o crea una sesión para el host"""
        pass
    
    @abstractmethod
    def release_session(self, session):
        """Libera una sesión"""
        pass
    
    @abstractmethod
    def close_all(self):
        """Cierra todas las sesiones activas"""
        pass


# ============================================================================
# INTERFACES DE CACHE
# ============================================================================
class ICacheProvider(ABC):
    """Interfaz para proveedores de cache"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del cache
        
        Args:
            key: Clave a buscar
            
        Returns:
            Valor almacenado o None si no existe/expiró
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 300):
        """
        Almacena un valor en el cache
        
        Args:
            key: Clave
            value: Valor a almacenar
            ttl: Time-to-live en segundos
        """
        pass
    
    @abstractmethod
    def invalidate(self, key: str):
        """Invalida/elimina una entrada del cache"""
        pass
    
    @abstractmethod
    def clear_all(self):
        """Limpia todo el cache"""
        pass


# ============================================================================
# INTERFACES DE LOGGING
# ============================================================================
class ILogger(ABC):
    """Interfaz para sistema de logging"""
    
    @abstractmethod
    def debug(self, message: str, **kwargs):
        """Log nivel DEBUG"""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs):
        """Log nivel INFO"""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs):
        """Log nivel WARNING"""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs):
        """Log nivel ERROR"""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs):
        """Log nivel CRITICAL"""
        pass


# ============================================================================
# INTERFACES DE RECURSOS
# ============================================================================
class IResourceManager(ABC):
    """Interfaz para gestión de recursos (archivos, instaladores)"""
    
    @abstractmethod
    def get_resource_path(self, resource_name: str) -> str:
        """Obtiene path de un recurso"""
        pass
    
    @abstractmethod
    def copy_to_remote(self, host: Host, resource_name: str, destination: str) -> bool:
        """Copia un recurso al host remoto"""
        pass
    
    @abstractmethod
    def verify_resource_exists(self, resource_name: str) -> bool:
        """Verifica si un recurso existe"""
        pass


# ============================================================================
# INTERFACES DE SCRIPT LOADER
# ============================================================================
class IScriptLoader(ABC):
    """Interfaz para carga de scripts PowerShell"""
    
    @abstractmethod
    def load(self, category: str, script_name: str) -> str:
        """
        Carga un script PowerShell desde archivo
        
        Args:
            category: Categoría (hardware, software, network, etc)
            script_name: Nombre del script (sin extensión)
            
        Returns:
            str: Contenido del script
        """
        pass
    
    @abstractmethod
    def load_with_wrapper(self, category: str, script_name: str) -> str:
        """Carga script con wrapper de error handling"""
        pass


# ============================================================================
# INTERFACES DE HEALTH CHECKS
# ============================================================================
class IHealthChecker(ABC):
    """Interfaz para health checks de hosts"""
    
    @abstractmethod
    def check_connectivity(self, host: Host) -> Dict[str, Any]:
        """Verifica conectividad básica"""
        pass
    
    @abstractmethod
    def check_disk_space(self, host: Host, required_gb: float) -> Dict[str, Any]:
        """Verifica espacio en disco disponible"""
        pass
    
    @abstractmethod
    def check_prerequisites(self, host: Host, operation: str) -> Dict[str, Any]:
        """Verifica pre-requisitos para una operación"""
        pass

