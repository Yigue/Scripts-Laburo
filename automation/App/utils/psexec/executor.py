"""
Ejecutor de comandos PsExec usando pypsexec
"""
from typing import Optional, Tuple
from dataclasses import dataclass
from .config import PsExecConfig


@dataclass
class ExecResult:
    """Resultado de ejecución de comando"""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    error: Optional[str] = None


class PsExecExecutor:
    """Ejecutor de comandos remotos usando PsExec (pypsexec)"""
    
    def __init__(self, config: Optional[PsExecConfig] = None):
        """
        Inicializa el ejecutor
        
        Args:
            config: Configuración PsExec (opcional)
        """
        self.config = config or PsExecConfig()
        self._last_error = None
    
    def execute(self, hostname: str, command: str, arguments: Optional[list] = None, timeout: int = 60) -> ExecResult:
        """
        Ejecuta un comando en el host remoto
        
        Args:
            hostname: Nombre del host remoto
            command: Comando a ejecutar
            arguments: Argumentos del comando como lista (opcional)
            timeout: Timeout en segundos
        
        Returns:
            ExecResult: Resultado de la ejecución
        """
        try:
            from pypsexec.client import Client
            
            # Si no hay credenciales, usar None (autenticación del usuario actual)
            # Esto funciona cuando el script se ejecuta como administrador
            if self.config.has_credentials():
                # pypsexec no acepta 'domain' como parámetro separado
                # El dominio debe estar en el username como "domain\\username"
                username = self.config.get_username() or self.config.username
                password = self.config.password
            else:
                # Sin credenciales: usar autenticación del usuario actual
                username = None
                password = None
            
            client = Client(
                hostname,
                username=username,
                password=password,
                encrypt=self.config.encrypt
            )
            
            try:
                client.connect()
                client.create_service()
                
                # Construir argumentos como string
                if arguments:
                    if isinstance(arguments, list):
                        args_str = " ".join(str(arg) for arg in arguments)
                    else:
                        args_str = str(arguments)
                else:
                    args_str = None
                
                # Ejecutar comando
                stdout, stderr, rc = client.run_executable(
                    command,
                    arguments=args_str,
                    use_system_account=self.config.use_system_account
                )
                
                stdout_text = stdout.decode(errors="ignore").strip() if stdout else ""
                stderr_text = stderr.decode(errors="ignore").strip() if stderr else ""
                
                success = rc == 0
                error = None if success else f"Comando falló con código {rc}"
                
                return ExecResult(
                    success=success,
                    stdout=stdout_text,
                    stderr=stderr_text,
                    return_code=rc,
                    error=error
                )
                
            finally:
                try:
                    client.remove_service()
                    client.disconnect()
                except:
                    pass
                    
        except ImportError as e:
            error = "pypsexec no está instalado. Ejecutá: pip install pypsexec"
            self._last_error = error
            return ExecResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error=error
            )
        except Exception as e:
            error = f"Error ejecutando comando: {str(e)}"
            self._last_error = error
            return ExecResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error=error
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
            from pypsexec.client import Client
            
            # Si no hay credenciales, usar None (autenticación del usuario actual)
            # Esto funciona cuando el script se ejecuta como administrador
            if self.config.has_credentials():
                # pypsexec no acepta 'domain' como parámetro separado
                # El dominio debe estar en el username como "domain\\username"
                username = self.config.get_username() or self.config.username
                password = self.config.password
            else:
                # Sin credenciales: usar autenticación del usuario actual
                username = None
                password = None
            
            client = Client(
                hostname,
                username=username,
                password=password,
                encrypt=self.config.encrypt
            )
            
            try:
                client.connect()
                client.create_service()
                
                # Ejecutar PowerShell con el script
                # Escapar comillas dobles en el script
                escaped_script = script.replace('"', '\\"')
                cmd = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& {{ {escaped_script} }}"'
                
                stdout, stderr, rc = client.run_executable(
                    "cmd.exe",
                    arguments=f'/c {cmd}',
                    use_system_account=self.config.use_system_account
                )
                
                stdout_text = stdout.decode(errors="ignore").strip() if stdout else ""
                stderr_text = stderr.decode(errors="ignore").strip() if stderr else ""
                
                success = rc == 0
                error = None if success else f"Script falló con código {rc}"
                
                return ExecResult(
                    success=success,
                    stdout=stdout_text,
                    stderr=stderr_text,
                    return_code=rc,
                    error=error
                )
                
            finally:
                try:
                    client.remove_service()
                    client.disconnect()
                except:
                    pass
                    
        except ImportError as e:
            error = "pypsexec no está instalado. Ejecutá: pip install pypsexec"
            self._last_error = error
            return ExecResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error=error
            )
        except Exception as e:
            error = f"Error ejecutando script: {str(e)}"
            self._last_error = error
            return ExecResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                error=error
            )
    
    def get_last_error(self) -> Optional[str]:
        """Retorna el último error ocurrido"""
        return self._last_error

