"""
Gestión de sesiones WinRM usando pypsrp con WSMan y RunspacePool
Sigue mejores prácticas para Active Directory
"""
from typing import Optional, Tuple, List
from .config import WinRMConfig


def _extract_info_message(info_obj) -> str:
    """Extrae un mensaje de objetos InformationRecord (Write-Host)."""
    if info_obj is None:
        return ""
    if isinstance(info_obj, str):
        return info_obj

    # pypsrp puede exponer diferentes estructuras según versión
    for attr in ("MessageData", "Message", "Data", "Text", "Value"):
        if hasattr(info_obj, attr):
            try:
                val = getattr(info_obj, attr)
                if val is None:
                    continue
                if isinstance(val, str):
                    return val
                return str(val)
            except Exception:
                continue

    try:
        s = str(info_obj)
        return "" if s in ("None", "NoneType") else s
    except Exception:
        return ""


def build_wsman(hostname: str, config: WinRMConfig, auth_method: Optional[str] = None):
    """Construye WSMan para pypsrp."""
    from pypsrp.wsman import WSMan
    from .connection import ensure_fqdn

    transport = auth_method or config.get_transport()
    if transport == "basic" and not config.use_ssl:
        raise ValueError("basic auth sin SSL es inseguro y normalmente está bloqueado (habilitá WINRM_SSL=true o cambia WINRM_AUTH).")

    fqdn_hostname = ensure_fqdn(hostname, config.domain, validate=True)

    # Si no hay credenciales configuradas, usar autenticación del usuario actual (SSO)
    if config.username and config.password:
        username = config.get_username()
        password = config.password
    else:
        username = None
        password = None
        transport = auth_method or "negotiate"

    return WSMan(
        server=fqdn_hostname,
        port=config.port,
        username=username,
        password=password,
        ssl=config.use_ssl,
        auth=transport,
        cert_validation=config.verify_ssl,
        operation_timeout=config.operation_timeout,
        read_timeout=config.read_timeout,
        connection_timeout=config.connection_timeout,
        encryption="always" if transport in ["negotiate", "kerberos", "ntlm"] else "never",
    )


class WinRMSession:
    """Gestiona sesiones WinRM persistentes usando RunspacePool"""

    def __init__(self, hostname: str, config: Optional[WinRMConfig] = None):
        self.hostname = hostname
        self.config = config or WinRMConfig()
        self._wsman = None
        self._pool = None

    def connect(self) -> bool:
        """Establece conexión con el host remoto."""
        try:
            from pypsrp.powershell import RunspacePool
            from pypsrp.exceptions import WinRMTransportError, AuthenticationError
            from .connection import test_network_access

            network_ok, network_error = test_network_access(self.hostname, ports=[self.config.port])
            if not network_ok:
                raise ConnectionError(f"Sin acceso de red: {network_error}")

            self._wsman = build_wsman(self.hostname, self.config)
            self._pool = RunspacePool(self._wsman)
            self._pool.open()
            return True

        except ImportError as e:
            raise ImportError("pypsrp no está instalado. Ejecutá: pip install pypsrp") from e
        except (WinRMTransportError, AuthenticationError) as e:
            error_msg = str(e)
            if "0xc0000234" in error_msg or "account is locked" in error_msg.lower():
                raise ConnectionError(f"⚠️ CUENTA BLOQUEADA: {error_msg}. Detené el script y contactá al administrador de AD.") from e
            raise ConnectionError(f"Error conectando a {self.hostname}: {error_msg}") from e
        except Exception as e:
            raise ConnectionError(f"Error inesperado: {str(e)}") from e

    def _invoke_script(self, script: str) -> Tuple[str, str, int]:
        if not self._pool:
            raise RuntimeError("Sesión no conectada. Llamá a connect() primero")

        from pypsrp.powershell import PowerShell

        ps = PowerShell(self._pool)

        # Hacer consistentes los errores (no-terminantes -> terminantes)
        ps.add_script("$ErrorActionPreference='Stop'\n" + script)
        ps.invoke()

        info_lines: List[str] = []
        if hasattr(ps.streams, "information") and ps.streams.information:
            for info in ps.streams.information:
                msg = _extract_info_message(info)
                if msg and msg.strip():
                    # Filtrar líneas de definición de función Write-Host
                    if msg.strip().startswith("param(") or "ForegroundColor" in msg:
                        continue
                    info_lines.append(msg)

        out_lines = [str(obj) for obj in (ps.output or [])]

        extra_lines: List[str] = []
        for stream_name in ("warning", "verbose", "debug"):
            stream = getattr(ps.streams, stream_name, None)
            if stream:
                extra_lines.extend([str(x) for x in stream])

        stdout = "\n".join([*info_lines, *out_lines, *extra_lines]).strip()

        err_objs = ps.streams.error or []
        stderr = "\n".join([str(e) for e in err_objs]).strip()

        return_code = 1 if err_objs else 0

        if self.config.debug and not stdout and not stderr:
            stderr = "[DEBUG] No output/error. Streams: " + ", ".join(
                f"{k}={len(getattr(ps.streams, k, []) or [])}" for k in ("information", "warning", "verbose", "debug", "error")
            )

        return stdout, stderr, return_code

    def execute(self, command: str, arguments: Optional[list] = None) -> Tuple[str, str, int]:
        """Ejecuta un comando en la sesión."""
        if arguments:
            args_str = " ".join(str(arg) for arg in arguments)
            script = f"{command} {args_str}"
        else:
            script = command
        return self._invoke_script(script)

    def execute_ps(self, script: str) -> Tuple[str, str, int]:
        """Ejecuta un script PowerShell."""
        return self._invoke_script(script)

    def close(self):
        """Cierra la sesión."""
        if self._pool:
            try:
                self._pool.close()
            except Exception:
                pass
            finally:
                self._pool = None
                self._wsman = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
