"""
Modelo de Host - Representación de un equipo remoto
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Host:
    """Representación de un host/equipo remoto"""
    
    hostname: str
    ip: Optional[str] = None
    is_online: bool = False
    last_seen: Optional[datetime] = None
    preferred_method: Optional[str] = None  # 'winrm', 'psexec', 'ansible'
    
    # Información adicional (opcional)
    os_version: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    
    def __str__(self) -> str:
        return f"Host({self.hostname}, online={self.is_online})"
    
    def __repr__(self) -> str:
        return f"Host(hostname='{self.hostname}', ip='{self.ip}', online={self.is_online})"
    
    @property
    def is_notebook(self) -> bool:
        """Determina si es notebook basado en el hostname (convenció NB*)"""
        return self.hostname.upper().startswith('NB')
    
    @property
    def is_pc(self) -> bool:
        """Determina si es PC basado en el hostname (convención PC*)"""
        return self.hostname.upper().startswith('PC')

