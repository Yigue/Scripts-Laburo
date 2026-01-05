"""
Test de conexión WinRM usando pypsrp con WSMan
Sigue mejores prácticas para Active Directory
"""
from typing import Tuple, Optional
import socket
from .config import WinRMConfig


def ensure_fqdn(hostname: str, domain: Optional[str] = None, validate: bool = True) -> str:
    """
    Asegura que el hostname sea FQDN (Fully Qualified Domain Name).
    Útil para Kerberos/Negotiate en Active Directory.

    Evitamos socket.getfqdn() ya que en entornos con DNS sucio puede devolver
    nombres obsoletos basados en la IP.
    """
    # Si ya tiene puntos, asumimos que es FQDN o IP
    if "." in hostname:
        return hostname

    # Si tenemos un dominio configurado, lo usamos como primera opción
    if domain:
        fqdn = f"{hostname}.{domain}"
        if validate:
            try:
                socket.gethostbyname(fqdn)
                return fqdn
            except socket.gaierror:
                # Si no resuelve con el dominio, devolvemos el original
                return hostname
        return fqdn

    # Si no hay dominio, devolvemos el hostname tal cual
    # No usamos socket.getfqdn() por los errores reportados de nombres incorrectos
    return hostname


def _tcp_probe(hostname: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return True
    except Exception:
        return False


def test_network_access(hostname: str, ports: Optional[list] = None) -> Tuple[bool, Optional[str]]:
    """
    Valida acceso de red básico antes de intentar WinRM.

    Importante: ping puede estar bloqueado. Por eso probamos también TCP.
    """
    ports = ports or [5985, 5986]

    # 1) Resolver DNS (si falla, igualmente puede funcionar por NetBIOS; no lo hacemos fatal)
    try:
        socket.gethostbyname(hostname)
    except Exception:
        pass

    # 2) Probar TCP a los puertos típicos de WinRM
    for p in ports:
        if _tcp_probe(hostname, p):
            return True, None

    # 3) Fallback: ping (no determinante)
    try:
        import subprocess
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "1500", hostname],
            capture_output=True,
            timeout=4
        )
        if result.returncode == 0:
            return True, None
    except Exception:
        pass

    return False, f"No hay respuesta en puertos WinRM {ports}. Posibles causas: Host apagado, Firewall bloqueando puertos, o WinRM deshabilitado en el equipo remoto."


def test_winrm_connection(hostname: str, config: Optional[WinRMConfig] = None) -> Tuple[bool, Optional[str]]:
    """
    Prueba la conexión WinRM con un host usando pypsrp.
    """
    if config is None:
        config = WinRMConfig()

    try:
        from pypsrp.wsman import WSMan
        from pypsrp.powershell import RunspacePool, PowerShell
        from pypsrp.exceptions import WinRMTransportError, AuthenticationError

        # 1. Validar acceso de red (evita bloqueos por reintentos)
        ports = [config.port] if config.port else [5985, 5986]
        network_ok, network_error = test_network_access(hostname, ports=ports)
        if not network_ok:
            return False, f"Sin acceso de red: {network_error}"

        # 2. Asegurar FQDN cuando sea posible
        fqdn_hostname = ensure_fqdn(hostname, config.domain, validate=False)
        if fqdn_hostname != hostname and "." in fqdn_hostname:
            try:
                socket.gethostbyname(fqdn_hostname)
            except socket.gaierror:
                fqdn_hostname = hostname

        # 3. Métodos de autenticación
        if not config.username or not config.password:
            auth_methods = ["negotiate"]
            username = None
            password = None
        else:
            username = config.get_username()
            password = config.password
            auth_methods = [config.get_transport()]
            if config.auth == "auto":
                auth_methods = ["negotiate", "ntlm"]

        last_error = None
        for auth_method in auth_methods:
            try:
                if auth_method == "basic" and not config.use_ssl:
                    return False, "basic auth sin SSL es inseguro y normalmente está bloqueado (habilitá SSL o cambia auth)."

                wsman = WSMan(
                    server=fqdn_hostname,
                    port=config.port,
                    username=username if (config.username and config.password) else None,
                    password=password if (config.username and config.password) else None,
                    ssl=config.use_ssl,
                    auth=auth_method,
                    cert_validation=config.verify_ssl,
                    connection_timeout=config.connection_timeout,
                    operation_timeout=config.operation_timeout,
                    read_timeout=config.read_timeout,
                    encryption="always" if auth_method in ["negotiate", "kerberos", "ntlm"] else "never",
                )

                with RunspacePool(wsman) as pool:
                    ps = PowerShell(pool)
                    ps.add_script("Write-Output 'TEST_OK'")
                    ps.invoke()

                    if ps.streams.error:
                        error_msg = "\n".join([str(e) for e in ps.streams.error])
                        last_error = f"Error de autenticación/ejecución: {error_msg}"
                        if auth_method == auth_methods[-1]:
                            return False, last_error
                        continue

                    output = "\n".join([str(x) for x in ps.output])
                    if "TEST_OK" in output:
                        return True, None

                    last_error = "Comando de prueba no devolvió resultado esperado"
                    if auth_method == auth_methods[-1]:
                        return False, last_error

            except AuthenticationError as e:
                error_msg = str(e)
                last_error = f"Error de autenticación: {error_msg}"

                if "0xc0000234" in error_msg or "account is locked" in error_msg.lower():
                    return False, f"⚠️ CUENTA BLOQUEADA: {error_msg}. Detené el script y contactá al administrador de AD."

                if auth_method == auth_methods[-1]:
                    return False, last_error

            except WinRMTransportError as e:
                return False, f"Error de transporte WinRM: {str(e)}"
            except Exception as e:
                last_error = f"Error de conexión: {str(e)}"
                if auth_method == auth_methods[-1]:
                    return False, last_error

        return False, last_error or "No se pudo establecer conexión con ningún método de autenticación"

    except ImportError:
        return False, "pypsrp no está instalado. Ejecutá: pip install pypsrp"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"
