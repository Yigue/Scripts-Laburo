"""
Gestión de sesiones WinRM usando pypsrp
"""
from typing import Optional, Tuple
from .config import WinRMConfig


class WinRMSession:
    """Gestiona sesiones WinRM persistentes"""
    
    def __init__(self, hostname: str, config: Optional[WinRMConfig] = None):
        """
        Inicializa una sesión WinRM
        
        Args:
            hostname: Nombre del host remoto
            config: Configuración WinRM
        """
        self.hostname = hostname
        self.config = config or WinRMConfig()
        self._client = None
    
    def connect(self) -> bool:
        """
        Establece conexión con el host remoto
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            from pypsrp.client import Client
            from pypsrp.exceptions import WinRMTransportError, AuthenticationError
            
            username = self.config.get_username()
            password = self.config.password if self.config.username else None
            auth_method = self.config.get_auth_method()
            
            self._client = Client(
                self.hostname,
                username=username,
                password=password,
                ssl=self.config.use_ssl,
                port=self.config.port,
                auth=auth_method,
                cert_validation=False,
                connection_timeout=30
            )
            
            return True
            
        except ImportError:
            raise ImportError("pypsrp no está instalado. Ejecutá: pip install pypsrp")
        except (WinRMTransportError, AuthenticationError) as e:
            raise ConnectionError(f"Error conectando a {self.hostname}: {str(e)}")
        except Exception as e:
            raise ConnectionError(f"Error inesperado: {str(e)}")
    
    def execute(self, command: str, arguments: Optional[list] = None) -> Tuple[str, str, int]:
        """
        Ejecuta un comando en la sesión
        
        Args:
            command: Comando a ejecutar
            arguments: Lista de argumentos (opcional)
        
        Returns:
            Tuple[str, str, int]: (stdout, stderr, return_code)
        """
        if not self._client:
            raise RuntimeError("Sesión no conectada. Llamá a connect() primero")
        
        try:
            if arguments:
                # pypsrp acepta argumentos como posicionales, no como keyword
                result = self._client.execute_cmd(command, *arguments)
            else:
                result = self._client.execute_cmd(command)
            
            stdout = result.stdout if result.stdout else ""
            stderr = result.stderr if result.stderr else ""
            return_code = result.rc
            
            return stdout, stderr, return_code
            
        except Exception as e:
            raise RuntimeError(f"Error ejecutando comando: {str(e)}")
    
    def execute_ps(self, script: str) -> Tuple[str, str, int]:
        """
        Ejecuta un script PowerShell
        
        Args:
            script: Script PowerShell a ejecutar
        
        Returns:
            Tuple[str, str, int]: (stdout, stderr, return_code)
        """
        if not self._client:
            raise RuntimeError("Sesión no conectada. Llamá a connect() primero")
        
        try:
            result = self._client.execute_ps(script)
            
            stdout = result.stdout if result.stdout else ""
            stderr = result.stderr if result.stderr else ""
            return_code = result.rc
            
            return stdout, stderr, return_code
            
        except Exception as e:
            raise RuntimeError(f"Error ejecutando script PowerShell: {str(e)}")
    
    def close(self):
        """Cierra la sesión"""
        if self._client:
            try:
                self._client.close()
            except:
                pass
            finally:
                self._client = None
    
    def __enter__(self):
        """Context manager: entrar"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: salir"""
        self.close()

