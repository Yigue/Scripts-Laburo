"""
Factories y Builders - Patrones creacionales
"""
from typing import Optional
from domain.models import Host, Task, OperationResult
from domain.interfaces import IRemoteExecutor
from config import AppConfig, get_config


class ExecutorFactory:
    """
    Factory para crear ejecutores remotos
    Implementa Factory Pattern
    """
    
    @staticmethod
    def create(method: str = "auto", config: Optional[AppConfig] = None) -> IRemoteExecutor:
        """
        Crea un ejecutor del tipo especificado
        
        Args:
            method: Tipo de executor ('winrm', 'psexec', 'ansible', 'auto')
            config: Configuración (usa global si no se provee)
            
        Returns:
            IRemoteExecutor: Instancia del executor
            
        Raises:
            ValueError: Si el método no es válido
        """
        if config is None:
            config = get_config()
        
        # Si es 'auto', usar RemoteExecutor con fallback
        if method == "auto":
            from utils.remote_executor import RemoteExecutor
            return RemoteExecutor(
                username=config.username if hasattr(config, 'username') else None,
                password=config.password if hasattr(config, 'password') else None
            )
        
        # Executors específicos
        if method == "winrm":
            from infrastructure.remote.executors import WinRMExecutor
            return WinRMExecutor(config)
        
        elif method == "psexec":
            from infrastructure.remote.executors import PsExecExecutor
            return PsExecExecutor(config)
        
        elif method == "ansible":
            from infrastructure.remote.executors import AnsibleExecutor
            return AnsibleExecutor(config)
        
        else:
            raise ValueError(f"Método de executor desconocido: {method}")
    
    @staticmethod
    def create_with_fallback(config: Optional[AppConfig] = None) -> IRemoteExecutor:
        """Crea executor con fallback automático WinRM → PsExec"""
        from utils.remote_executor import RemoteExecutor
        return RemoteExecutor()


class HostBuilder:
    """
    Builder para crear objetos Host
    Implementa Builder Pattern
    """
    
    def __init__(self):
        self._hostname = ""
        self._ip = None
        self._is_online = False
        self._preferred_method = None
    
    def with_hostname(self, hostname: str):
        """Define hostname"""
        self._hostname = hostname
        return self
    
    def with_ip(self, ip: str):
        """Define IP"""
        self._ip = ip
        return self
    
    def online(self, is_online: bool = True):
        """Define si está online"""
        self._is_online = is_online
        return self
    
    def with_preferred_method(self, method: str):
        """Define método preferido de conexión"""
        self._preferred_method = method
        return self
    
    def build(self) -> Host:
        """Construye el objeto Host"""
        return Host(
            hostname=self._hostname,
            ip=self._ip,
            is_online=self._is_online,
            preferred_method=self._preferred_method
        )


class TaskBuilder:
    """
    Builder para crear objetos Task
    Simplifica creación de tareas complejas
    """
    
    def __init__(self):
        self._hostname = ""
        self._operation = ""
        self._metadata = {}
    
    def for_host(self, hostname: str):
        """Define host donde ejecutar"""
        self._hostname = hostname
        return self
    
    def operation(self, operation: str):
        """Define operación a ejecutar"""
        self._operation = operation
        return self
    
    def with_metadata(self, key: str, value):
        """Agrega metadata"""
        self._metadata[key] = value
        return self
    
    def build(self) -> Task:
        """Construye el objeto Task"""
        return Task(
            hostname=self._hostname,
            operation=self._operation,
            metadata=self._metadata
        )


class OperationResultBuilder:
    """Builder para OperationResult"""
    
    def __init__(self):
        self._success = False
        self._message = ""
        self._data = None
        self._errors = []
        self._warnings = []
        self._metadata = {}
    
    def success(self, is_success: bool = True):
        """Define si fue exitoso"""
        self._success = is_success
        return self
    
    def message(self, message: str):
        """Define mensaje"""
        self._message = message
        return self
    
    def with_data(self, data):
        """Agrega data"""
        self._data = data
        return self
    
    def add_error(self, error: str):
        """Agrega error"""
        self._errors.append(error)
        self._success = False
        return self
    
    def add_warning(self, warning: str):
        """Agrega warning"""
        self._warnings.append(warning)
        return self
    
    def build(self) -> OperationResult:
        """Construye el resultado"""
        return OperationResult(
            success=self._success,
            message=self._message,
            data=self._data,
            errors=self._errors,
            warnings=self._warnings,
            metadata=self._metadata
        )


