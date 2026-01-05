"""
Configuración para WinRM usando pypsrp
"""
import os
from typing import Optional
from pathlib import Path

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv

    current_file = Path(__file__).resolve()
    
    # Buscar el archivo .env subiendo niveles hasta encontrarlo o llegar a la raíz
    env_file = None
    for parent in current_file.parents:
        potential_env = parent / ".env"
        if potential_env.exists():
            env_file = potential_env
            break
            
    if env_file:
        load_dotenv(env_file)
    else:
        # Si no se encuentra explícitamente, intentar el default de load_dotenv
        load_dotenv()

except ImportError:
    # python-dotenv no está instalado, usar solo variables de entorno del sistema
    pass


class WinRMConfig:
    """Configuración para conexiones WinRM (pypsrp)"""

    def __init__(self):
        # Si WINRM_USE_SYSTEM_AUTH está en "true", ignorar credenciales y usar autenticación del sistema
        use_system_auth = os.getenv("WINRM_USE_SYSTEM_AUTH", "false").lower() == "true"

        if use_system_auth:
            self.username = None
            self.password = None
            self.domain = None
        else:
            self.username = (os.getenv("WINRM_USER") or os.getenv("PSEXEC_USER") or "").strip() or None
            self.password = (os.getenv("WINRM_PASS") or os.getenv("PSEXEC_PASS") or "").strip() or None
            self.domain = (os.getenv("WINRM_DOMAIN") or os.getenv("PSEXEC_DOMAIN") or "").strip() or None

        self.use_ssl = os.getenv("WINRM_SSL", "false").lower() == "true"

        # Permitir override explícito de puerto
        default_port = "5986" if self.use_ssl else "5985"
        self.port = int(os.getenv("WINRM_PORT", default_port))

        # auto | kerberos | ntlm | credssp | basic | negotiate
        self.auth = os.getenv("WINRM_AUTH", "auto").lower()

        # Parámetros WSMan
        # Seguridad: por defecto, si usás SSL conviene validar certificados.
        # En lab podés poner WINRM_VERIFY_SSL=false.
        verify_default = "true" if self.use_ssl else "false"
        self.verify_ssl = os.getenv("WINRM_VERIFY_SSL", verify_default).lower() == "true"

        self.operation_timeout = int(os.getenv("WINRM_OPERATION_TIMEOUT", "30"))
        self.read_timeout = int(os.getenv("WINRM_READ_TIMEOUT", "30"))
        self.connection_timeout = int(os.getenv("WINRM_CONNECTION_TIMEOUT", "30"))

        # Debug de streams/diagnóstico
        self.debug = os.getenv("WINRM_DEBUG", "false").lower() == "true"

    def get_auth_method(self) -> str:
        """
        Determina el método de autenticación preferido (alto nivel).

        Nota: en pypsrp, para AD/Windows lo más robusto suele ser 'negotiate'.
        """
        if self.auth != "auto":
            return self.auth

        # Auto-detección (alto nivel)
        if not self.username or not self.password:
            # Sin credenciales: se intentará SSO del usuario actual
            return "kerberos"

        username = self.get_username() or self.username
        if username and "\\" in username:
            return "kerberos"

        return "ntlm"

    def get_transport(self) -> str:
        """
        Retorna el transporte para WSMan/pypsrp.

        Recomendación práctica:
        - En AD/Windows: 'negotiate' (deja que SSPI elija Kerberos/NTLM)
        - Sin credenciales: 'negotiate' para SSO
        """
        if self.auth != "auto":
            return self.auth

        # SSO o AD: negotiate suele ser el camino más estable
        return "negotiate"

    def get_username(self) -> Optional[str]:
        """
        Retorna username formateado con dominio si aplica.
        Si el username ya contiene el dominio (ej: "domain\\user"), lo retorna tal cual.
        """
        if not self.username:
            return None

        if "\\" in self.username:
            return self.username

        if self.domain:
            return f"{self.domain}\\{self.username}"

        return self.username
