"""
Configuración para PsExec usando pypsexec
"""
import os
from typing import Optional
from pathlib import Path

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    # Buscar .env en la raíz del proyecto
    # El proyecto está en: Scripts-Laburo/
    # Este archivo está en: Scripts-Laburo/automation/python/utils/psexec/
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


class PsExecConfig:
    """Configuración para conexiones PsExec"""
    
    def __init__(self):
        """Inicializa configuración desde variables de entorno"""
        self.username = os.getenv("PSEXEC_USER") or os.getenv("WINRM_USER")
        self.password = os.getenv("PSEXEC_PASS") or os.getenv("WINRM_PASS")
        self.domain = os.getenv("PSEXEC_DOMAIN") or os.getenv("WINRM_DOMAIN")
        self.encrypt = os.getenv("PSEXEC_ENCRYPT", "false").lower() == "true"
        self.use_system_account = os.getenv("PSEXEC_SYSTEM", "true").lower() == "true"
        
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
    
    def has_credentials(self) -> bool:
        """Verifica si hay credenciales configuradas"""
        return bool(self.username and self.password)

