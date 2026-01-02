"""
Ejecutor de comandos WinRM usando pypsrp
"""
from typing import Optional, Tuple
from dataclasses import dataclass
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
        """
        Inicializa el ejecutor
        
        Args:
            config: Configuración WinRM (opcional)
        """
        self.config = config or WinRMConfig()
        self._last_error = None
    
    def execute(self, hostname: str, command: str, arguments: Optional[list] = None, timeout: int = 60) -> ExecResult:
        """
        Ejecuta un comando en el host remoto
        
        Args:
            hostname: Nombre del host remoto
            command: Comando a ejecutar
            arguments: Argumentos del comando (opcional)
            timeout: Timeout en segundos
        
        Returns:
            ExecResult: Resultado de la ejecución
        """
        try:
            session = WinRMSession(hostname, self.config)
            session.connect()
            
            try:
                stdout, stderr, return_code = session.execute(command, arguments)
                
                success = return_code == 0
                error = None if success else f"Comando falló con código {return_code}"
                
                return ExecResult(
                    success=success,
                    stdout=stdout,
                    stderr=stderr,
                    return_code=return_code,
                    error=error
                )
            finally:
                session.close()
                
        except ImportError as e:
            self._last_error = str(e)
            return ExecResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error=str(e)
            )
        except ConnectionError as e:
            self._last_error = str(e)
            return ExecResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error=str(e)
            )
        except Exception as e:
            self._last_error = str(e)
            return ExecResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error=f"Error inesperado: {str(e)}"
            )
    
    def execute_ps(self, hostname: str, script: str, timeout: int = 120) -> ExecResult:
        """
        Ejecuta un script PowerShell en el host remoto
        
        Args:
            hostname: Nombre del host remoto
            script: Script PowerShell a ejecutar
            timeout: Timeout en segundos
        
        Returns:
            ExecResult: Resultado de la ejecución
        """
        try:
            session = WinRMSession(hostname, self.config)
            session.connect()
            
            try:
                stdout, stderr, return_code = session.execute_ps(script)
                
                success = return_code == 0
                error = None if success else f"Script falló con código {return_code}"
                
                return ExecResult(
                    success=success,
                    stdout=stdout,
                    stderr=stderr,
                    return_code=return_code,
                    error=error
                )
            finally:
                session.close()
                
        except ImportError as e:
            self._last_error = str(e)
            return ExecResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error=str(e)
            )
        except ConnectionError as e:
            self._last_error = str(e)
            return ExecResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error=str(e)
            )
        except Exception as e:
            self._last_error = str(e)
            return ExecResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error=f"Error inesperado: {str(e)}"
            )
    
    def get_last_error(self) -> Optional[str]:
        """Retorna el último error ocurrido"""
        return self._last_error

