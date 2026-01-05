"""
Decoradores reutilizables para la aplicación
Incluye @retry, @validate_inputs, etc.
"""
import time
import functools
from typing import Callable, Any, Type, Tuple
from .constants import MAX_RETRY_ATTEMPTS, RETRY_DELAY, RETRY_BACKOFF
from .exceptions import AutomationError


def retry(
    max_attempts: int = MAX_RETRY_ATTEMPTS,
    delay: float = RETRY_DELAY,
    backoff: float = RETRY_BACKOFF,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorador para reintentar una función en caso de fallo
    
    Args:
        max_attempts: Número máximo de intentos
        delay: Delay inicial entre intentos (segundos)
        backoff: Multiplicador de delay (ej: 2 = delay se duplica cada intento)
        exceptions: Tupla de excepciones a capturar
        
    Example:
        @retry(max_attempts=3, delay=2, backoff=2)
        def connect_to_host(hostname):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        # Último intento falló, propagar excepción
                        raise
            
            # Esto no debería alcanzarse, pero por si acaso
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def validate_hostname(func: Callable) -> Callable:
    """
    Decorador para validar que el primer argumento sea un hostname válido
    
    Example:
        @validate_hostname
        def connect(hostname: str):
            ...
    """
    from .validators import validate_hostname as validate
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if args:
            hostname = args[0]
            validate(hostname, raise_on_invalid=True)
        return func(*args, **kwargs)
    return wrapper


def log_execution(logger=None):
    """
    Decorador para loguear ejecución de funciones
    
    Args:
        logger: Logger a usar (opcional, usa print si no se provee)
        
    Example:
        @log_execution(logger=my_logger)
        def important_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            log_func = logger.info if logger else print
            
            log_func(f"Ejecutando: {func_name}")
            try:
                result = func(*args, **kwargs)
                log_func(f"Completado: {func_name}")
                return result
            except Exception as e:
                error_func = logger.error if logger else print
                error_func(f"Error en {func_name}: {e}")
                raise
        return wrapper
    return decorator


def measure_time(func: Callable) -> Callable:
    """
    Decorador para medir tiempo de ejecución
    
    Example:
        @measure_time
        def slow_operation():
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"{func.__name__} tomó {elapsed:.2f} segundos")
        return result
    return wrapper


def deprecated(message: str = "Esta función está deprecada"):
    """
    Decorador para marcar funciones como deprecadas
    
    Args:
        message: Mensaje a mostrar
        
    Example:
        @deprecated("Usar nueva_funcion() en su lugar")
        def vieja_funcion():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            warnings.warn(f"{func.__name__} is deprecated. {message}", DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator

