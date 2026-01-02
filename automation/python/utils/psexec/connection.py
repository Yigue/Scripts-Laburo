"""
Test de conexión PsExec usando pypsexec
"""
import subprocess
from typing import Tuple, Optional, Dict
from .config import PsExecConfig


def test_ping(hostname: str, timeout: int = 3) -> bool:
    """
    Prueba conectividad básica con ping
    
    Args:
        hostname: Nombre del host
        timeout: Timeout en segundos
    
    Returns:
        bool: True si responde al ping
    """
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout * 1000), hostname],
            capture_output=True,
            text=True,
            timeout=timeout + 2
        )
        return result.returncode == 0
    except Exception:
        return False


def test_port_445(hostname: str) -> bool:
    """
    Prueba si el puerto 445 (SMB) está abierto
    
    Args:
        hostname: Nombre del host
    
    Returns:
        bool: True si el puerto está abierto
    """
    try:
        cmd = f"(Test-NetConnection -ComputerName {hostname} -Port 445).TcpTestSucceeded"
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=8
        )
        return result.returncode == 0 and "True" in result.stdout
    except Exception:
        return False


def test_psexec_connection(hostname: str, config: Optional[PsExecConfig] = None) -> Tuple[bool, Optional[str], Dict]:
    """
    Prueba la conexión PsExec con un host usando pypsexec
    
    Args:
        hostname: Nombre del host remoto
        config: Configuración PsExec (opcional)
    
    Returns:
        Tuple[bool, Optional[str], Dict]: (éxito, mensaje_error, detalles)
    """
    if config is None:
        config = PsExecConfig()
    
    details = {
        "ping": False,
        "port_445": False,
        "credentials": False,
        "connection": False
    }
    
    # Verificar credenciales
    if not config.has_credentials():
        return False, "No hay credenciales configuradas (PSEXEC_USER/PSEXEC_PASS)", details
    
    details["credentials"] = True
    
    # Verificar ping
    details["ping"] = test_ping(hostname)
    if not details["ping"]:
        return False, "El host no responde al ping", details
    
    # Verificar puerto 445
    details["port_445"] = test_port_445(hostname)
    if not details["port_445"]:
        return False, "Puerto 445 (SMB) no está accesible", details
    
    # Intentar conexión real con pypsexec
    try:
        from pypsexec.client import Client
        
        # pypsexec no acepta 'domain' como parámetro separado
        # El dominio debe estar en el username como "domain\username"
        username = config.get_username() or config.username
        
        client = Client(
            hostname,
            username=username,
            password=config.password,
            encrypt=config.encrypt
        )
        
        try:
            client.connect()
            client.create_service()
            
            # Test simple: ejecutar echo
            stdout, stderr, rc = client.run_executable(
                "cmd.exe",
                arguments="/c echo CONNECTION_OK",
                timeout=10,
                use_system_account=config.use_system_account
            )
            
            details["connection"] = (rc == 0 and b"CONNECTION_OK" in stdout)
            
            if details["connection"]:
                return True, None, details
            else:
                return False, f"Comando de prueba falló (código {rc})", details
                
        finally:
            try:
                client.remove_service()
                client.disconnect()
            except:
                pass
                
    except ImportError:
        return False, "pypsexec no está instalado. Ejecutá: pip install pypsexec", details
    except Exception as e:
        error_msg = str(e)
        if "Access is denied" in error_msg or "denied" in error_msg.lower():
            return False, "Acceso denegado - verificá credenciales", details
        elif "could not connect" in error_msg.lower() or "connection" in error_msg.lower():
            return False, f"Error de conexión: {error_msg}", details
        else:
            return False, f"Error: {error_msg}", details

