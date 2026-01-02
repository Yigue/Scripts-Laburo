"""
Módulos de administración remota organizados por categorías.
"""

from . import consola_remota
from .hardware import (
    system_info,
    configurar_equipo,
    optimizar,
    reiniciar,
    dell_command,
    activar_windows,
)
from .redes import wcorp_fix
from .impresoras import impresoras, zebra_calibrar
from .software import office_install, aplicaciones

__all__ = [
    "consola_remota",
    "system_info",
    "configurar_equipo",
    "optimizar",
    "reiniciar",
    "dell_command",
    "activar_windows",
    "wcorp_fix",
    "impresoras",
    "zebra_calibrar",
    "office_install",
    "aplicaciones",
]
