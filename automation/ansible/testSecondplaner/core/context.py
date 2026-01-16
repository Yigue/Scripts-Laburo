"""
Sistema de contexto persistente para mantener el estado de la sesión
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv, set_key, find_dotenv


class AppContext:
    """Contexto de aplicación que persiste el estado de la sesión"""
    
    def __init__(self, env_file: Optional[Path] = None):
        """
        Inicializar contexto
        
        Args:
            env_file: Archivo .env donde guardar el contexto (None = usar .env en raíz del proyecto)
        """
        self.env_file = env_file or Path(__file__).parent.parent.parent / ".env"
        self._session_file = Path(__file__).parent.parent / "config" / "session.env"
        
        # Estado de sesión
        self.target: Optional[str] = None
        self.targets: List[str] = []
        self.read_only_mode: bool = False
        self.check_mode: bool = False
        self.verbosity: int = 0
        self.wlc_profile: Optional[str] = None
        self.last_result: Optional[str] = None  # OK, FAIL, WARN
        self.credentials_profile: Optional[str] = None
        
        # Cargar contexto al inicializar
        self.load()
    
    def load(self) -> None:
        """Cargar contexto desde archivo .env"""
        # Intentar cargar desde session.env primero (sesión actual)
        if self._session_file.exists():
            load_dotenv(self._session_file, override=True)
        
        # Luego cargar desde .env general (configuración persistente)
        if self.env_file.exists():
            load_dotenv(self.env_file)
        
        # Cargar valores
        self.target = os.getenv("IT_OPS_TARGET")
        targets_str = os.getenv("IT_OPS_TARGETS", "")
        self.targets = [t.strip() for t in targets_str.split(",") if t.strip()]
        self.read_only_mode = os.getenv("IT_OPS_READ_ONLY", "false").lower() == "true"
        self.check_mode = os.getenv("IT_OPS_CHECK_MODE", "false").lower() == "true"
        self.verbosity = int(os.getenv("IT_OPS_VERBOSITY", "0"))
        self.wlc_profile = os.getenv("IT_OPS_WLC_PROFILE")
        self.last_result = os.getenv("IT_OPS_LAST_RESULT")
        self.credentials_profile = os.getenv("IT_OPS_CREDENTIALS_PROFILE")
    
    def save(self, persist: bool = False) -> None:
        """
        Guardar contexto en archivo
        
        Args:
            persist: Si True, guarda en .env general. Si False, solo en session.env
        """
        target_file = self.env_file if persist else self._session_file
        
        # Asegurar que el directorio existe
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Guardar valores
        if self.target:
            set_key(str(target_file), "IT_OPS_TARGET", self.target)
        if self.targets:
            set_key(str(target_file), "IT_OPS_TARGETS", ",".join(self.targets))
        
        set_key(str(target_file), "IT_OPS_READ_ONLY", str(self.read_only_mode).lower())
        set_key(str(target_file), "IT_OPS_CHECK_MODE", str(self.check_mode).lower())
        set_key(str(target_file), "IT_OPS_VERBOSITY", str(self.verbosity))
        
        if self.wlc_profile:
            set_key(str(target_file), "IT_OPS_WLC_PROFILE", self.wlc_profile)
        if self.last_result:
            set_key(str(target_file), "IT_OPS_LAST_RESULT", self.last_result)
        if self.credentials_profile:
            set_key(str(target_file), "IT_OPS_CREDENTIALS_PROFILE", self.credentials_profile)
    
    def reset(self) -> None:
        """Limpiar contexto (mantiene solo configuración persistente)"""
        self.target = None
        self.targets = []
        self.last_result = None
        self.save(persist=False)
    
    def set_target(self, target: str) -> None:
        """Establecer target activo"""
        self.target = target.upper() if target else None
        self.save()
    
    def add_targets(self, targets: List[str]) -> None:
        """Agregar targets a la lista bulk"""
        new_targets = [t.upper() if t else None for t in targets if t]
        self.targets.extend(new_targets)
        self.targets = list(set(self.targets))  # Eliminar duplicados
        self.save()
    
    def clear_targets(self) -> None:
        """Limpiar lista de targets"""
        self.targets = []
        self.save()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir contexto a diccionario para visualización"""
        return {
            "target": self.target or "No seteado",
            "targets_count": len(self.targets),
            "read_only_mode": "ON" if self.read_only_mode else "OFF",
            "check_mode": "ON" if self.check_mode else "OFF",
            "verbosity": self.verbosity,
            "wlc_profile": self.wlc_profile or "No seteado",
            "last_result": self.last_result or "-",
            "credentials_profile": self.credentials_profile or "Default"
        }
