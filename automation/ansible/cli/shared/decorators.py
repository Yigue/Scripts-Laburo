# -*- coding: utf-8 -*-
"""
shared/decorators.py
====================
Decoradores útiles para la aplicación.
"""

import time
import functools
from typing import Callable, Any


def retry(max_attempts: int = 3, delay: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorador para reintentar una función si falla.
    
    Args:
        max_attempts: Número máximo de intentos
        delay: Segundos a esperar entre intentos
        exceptions: Tupla de excepciones a capturar para reintentar
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(delay)
                        continue
                    raise
            raise last_exception
        return wrapper
    return decorator
