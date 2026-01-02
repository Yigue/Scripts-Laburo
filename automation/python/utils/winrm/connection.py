"""
Test de conexión WinRM usando pypsrp
"""
from typing import Tuple, Optional
from .config import WinRMConfig


def test_winrm_connection(hostname: str, config: Optional[WinRMConfig] = None) -> Tuple[bool, Optional[str]]:
    """
    Prueba la conexión WinRM con un host usando pypsrp
    
    Args:
        hostname: Nombre del host remoto
        config: Configuración WinRM (opcional, usa defaults si no se proporciona)
    
    Returns:
        Tuple[bool, Optional[str]]: (éxito, mensaje_error)
    """
    if config is None:
        config = WinRMConfig()
    
    try:
        from pypsrp.client import Client
        from pypsrp.exceptions import WinRMTransportError, AuthenticationError
        
        # Intentar con diferentes métodos de autenticación
        auth_methods = [config.get_auth_method()]
        if auth_methods[0] == "auto":
            auth_methods = ["kerberos", "ntlm"]  # Intentar ambos
        
        for auth_method in auth_methods:
            try:
                username = config.get_username()
                password = config.password if config.username else None
                
                client = Client(
                    hostname,
                    username=username,
                    password=password,
                    ssl=config.use_ssl,
                    port=config.port,
                    auth=auth_method,
                    cert_validation=False,
                    connection_timeout=10
                )
                
                # Test simple: obtener nombre del equipo
                result = client.execute_cmd("echo", "TEST")
                client.close()
                
                return True, None
                
            except AuthenticationError as e:
                if auth_method == auth_methods[-1]:  # Último método
                    return False, f"Error de autenticación: {str(e)}"
                continue  # Intentar siguiente método
                
            except WinRMTransportError as e:
                return False, f"Error de transporte WinRM: {str(e)}"
                
            except Exception as e:
                if auth_method == auth_methods[-1]:  # Último método
                    return False, f"Error de conexión: {str(e)}"
                continue
        
        return False, "No se pudo establecer conexión con ningún método de autenticación"
        
    except ImportError:
        return False, "pypsrp no está instalado. Ejecutá: pip install pypsrp"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"

