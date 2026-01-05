"""
Excepciones personalizadas para la aplicación
Jerarquía de excepciones para mejor manejo de errores
"""


class AutomationError(Exception):
    """Excepción base para todos los errores de automatización"""
    pass


class ConnectionError(AutomationError):
    """Error de conexión al host remoto"""
    pass


class TimeoutError(AutomationError):
    """Timeout ejecutando operación remota"""
    pass


class ValidationError(AutomationError):
    """Error de validación de inputs/parámetros"""
    pass


class ResourceNotFoundError(AutomationError):
    """Recurso no encontrado (archivo, instalador, etc)"""
    pass


class PermissionError(AutomationError):
    """Error de permisos insuficientes"""
    pass


class RemoteExecutionError(AutomationError):
    """Error ejecutando comando/script en host remoto"""
    pass


class ConfigurationError(AutomationError):
    """Error de configuración"""
    pass


class DependencyError(AutomationError):
    """Dependencia no satisfecha (librería, herramienta, etc)"""
    pass


class NetworkError(AutomationError):
    """Error de red (DNS, conectividad, etc)"""
    pass


class AuthenticationError(AutomationError):
    """Error de autenticación"""
    pass


class CacheError(AutomationError):
    """Error relacionado con cache"""
    pass


class ScriptLoadError(AutomationError):
    """Error cargando script PowerShell"""
    pass

