"""
Ejecutor de comandos WinRM usando pypsrp
"""
from typing import Optional
from dataclasses import dataclass
import copy

from .config import WinRMConfig
from .session import WinRMSession


@dataclass
class ExecResult:
    """Resultado de ejecución de comando"""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    error: Optional[str] = None


class WinRMExecutor:
    """Ejecutor de comandos remotos usando WinRM (pypsrp)"""

    def __init__(self, config: Optional[WinRMConfig] = None):
        self.config = config or WinRMConfig()
        self._last_error = None

    def _config_with_timeout(self, timeout: int) -> WinRMConfig:
        """Crea una copia de la configuración con timeouts ajustados por llamada."""
        cfg = copy.copy(self.config)
        cfg.read_timeout = max(int(timeout), 1)
        cfg.operation_timeout = max(int(timeout), 1)
        return cfg

    def execute(self, hostname: str, command: str, arguments: Optional[list] = None, timeout: int = 60) -> ExecResult:
        try:
            session = WinRMSession(hostname, self._config_with_timeout(timeout))
            session.connect()
            try:
                stdout, stderr, return_code = session.execute(command, arguments)
                success = return_code == 0
                error = None if success else f"Comando falló con código {return_code}"
                return ExecResult(success=success, stdout=stdout, stderr=stderr, return_code=return_code, error=error)
            finally:
                session.close()

        except (ImportError, ConnectionError) as e:
            self._last_error = str(e)
            return ExecResult(success=False, stdout="", stderr="", return_code=-1, error=str(e))
        except Exception as e:
            self._last_error = str(e)
            return ExecResult(success=False, stdout="", stderr="", return_code=-1, error=f"Error inesperado: {str(e)}")

    def execute_ps(self, hostname: str, script: str, timeout: int = 120) -> ExecResult:
        try:
            session = WinRMSession(hostname, self._config_with_timeout(timeout))
            session.connect()
            try:
                stdout, stderr, return_code = session.execute_ps(script)
                success = return_code == 0
                error = None if success else f"Script falló con código {return_code}"
                return ExecResult(success=success, stdout=stdout, stderr=stderr, return_code=return_code, error=error)
            finally:
                session.close()

        except (ImportError, ConnectionError) as e:
            self._last_error = str(e)
            return ExecResult(success=False, stdout="", stderr="", return_code=-1, error=str(e))
        except Exception as e:
            self._last_error = str(e)
            return ExecResult(success=False, stdout="", stderr="", return_code=-1, error=f"Error inesperado: {str(e)}")

    def get_last_error(self) -> Optional[str]:
        return self._last_error
