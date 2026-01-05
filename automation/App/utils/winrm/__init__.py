"""
Módulo WinRM - PowerShell Remoting Protocol usando pypsrp
Proporciona funcionalidades para conexión y ejecución remota usando WinRM
"""

from .connection import test_winrm_connection
from .executor import WinRMExecutor
from .session import WinRMSession
from .config import WinRMConfig

__all__ = [
    'test_winrm_connection',
    'WinRMExecutor',
    'WinRMSession',
    'WinRMConfig',
]

