"""
Configuración para WinRM usando pypsrp
"""
import os
from typing import Optional
from pathlib import Path

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    # Buscar .env en la raíz del proyecto
    # El proyecto está en: Scripts-Laburo/
    # Este archivo está en: Scripts-Laburo/automation/python/utils/winrm/
    # Buscamos .env subiendo 4 niveles
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent  # Subir hasta Scripts-Laburo/
    env_file = project_root / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Fallback: buscar en el directorio actual o padre
        load_dotenv()
except ImportError:
    # python-dotenv no está instalado, usar solo variables de entorno del sistema
    pass


class WinRMConfig:
    """Configuración para conexiones WinRM"""
    
    def __init__(self):
        """Inicializa configuración desde variables de entorno"""
        self.username = os.getenv("WINRM_USER") or os.getenv("PSEXEC_USER")
        self.password = os.getenv("WINRM_PASS") or os.getenv("PSEXEC_PASS")
        self.domain = os.getenv("WINRM_DOMAIN") or os.getenv("PSEXEC_DOMAIN")
        self.use_ssl = os.getenv("WINRM_SSL", "false").lower() == "true"
        self.port = 5986 if self.use_ssl else 5985
        self.auth = os.getenv("WINRM_AUTH", "auto").lower()  # auto, kerberos, ntlm, credssp, basic
        
    def get_auth_method(self) -> str:
        """
        Determina el método de autenticación a usar
        
        Returns:
            str: Método de autenticación (kerberos, ntlm, credssp, basic)
        """
        if self.auth != "auto":
            return self.auth
        
        # Auto-detección: 
        # - Si hay dominio en el username o configurado, intentar Kerberos primero
        # - Si no hay dominio, usar NTLM
        username = self.get_username() or self.username
        if username and "\\" in username:
            # Hay dominio, intentar Kerberos primero (más seguro para dominios)
            return "kerberos"
        elif self.username and self.password:
            # Hay credenciales pero sin dominio, usar NTLM
            return "ntlm"
        return "kerberos"
    
    def get_username(self) -> Optional[str]:
        """
        Retorna username formateado con dominio si aplica
        Si el username ya contiene el dominio (ej: "domain\user"), lo retorna tal cual
        """
        if not self.username:
            return None
        
        # Si el username ya tiene dominio (contiene \), retornarlo tal cual
        if "\\" in self.username:
            return self.username
        
        # Si hay dominio configurado, agregarlo
        if self.domain:
            return f"{self.domain}\\{self.username}"
        
        return self.username

