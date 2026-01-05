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


class PsExecConfig:
    """Configuración para conexiones PsExec"""
    
    def __init__(self):
        """Inicializa configuración desde variables de entorno"""
        # Si PSEXEC_USE_SYSTEM_AUTH está en "true", ignorar credenciales y usar autenticación del sistema
        use_system_auth = os.getenv("PSEXEC_USE_SYSTEM_AUTH") or os.getenv("WINRM_USE_SYSTEM_AUTH", "false")
        use_system_auth = use_system_auth.lower() == "true"
        
        if use_system_auth:
            # Usar autenticación del sistema (ignorar credenciales del .env)
            self.username = None
            self.password = None
            self.domain = None
        else:
            # Solo usar valores si están realmente configurados (no vacíos)
            self.username = (os.getenv("PSEXEC_USER") or os.getenv("WINRM_USER") or "").strip() or None
            self.password = (os.getenv("PSEXEC_PASS") or os.getenv("WINRM_PASS") or "").strip() or None
            self.domain = (os.getenv("PSEXEC_DOMAIN") or os.getenv("WINRM_DOMAIN") or "").strip() or None
        self.encrypt = os.getenv("PSEXEC_ENCRYPT", "false").lower() == "true"
        self.use_system_account = os.getenv("PSEXEC_SYSTEM", "true").lower() == "true"
        
    def get_username(self) -> Optional[str]:
        """
        Retorna username formateado con dominio si aplica
        Si el username ya contiene el dominio (ej: "domain\\user"), lo retorna tal cual
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

