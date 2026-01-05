"""
SessionPool - Pool de conexiones remotas reutilizables
Mejora performance al mantener sesiones abiertas
"""
import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from infrastructure.logging import get_logger
from config import get_config


@dataclass
class PooledSession:
    """Sesión en el pool"""
    hostname: str
    session: any
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    use_count: int = 0
    is_active: bool = True
    
    def mark_used(self):
        """Marca la sesión como usada"""
        self.last_used = datetime.now()
        self.use_count += 1
    
    @property
    def idle_time(self) -> float:
        """Retorna tiempo de inactividad en segundos"""
        return (datetime.now() - self.last_used).total_seconds()
    
    @property
    def age(self) -> float:
        """Retorna edad de la sesión en segundos"""
        return (datetime.now() - self.created_at).total_seconds()


class SessionPool:
    """
    Pool de sesiones remotas reutilizables
    Mejora performance al evitar crear/destruir sesiones constantemente
    """
    
    def __init__(self, max_sessions: int = 10, idle_timeout: int = 300, max_age: int = 3600):
        """
        Inicializa el pool
        
        Args:
            max_sessions: Máximo de sesiones simultáneas
            idle_timeout: Timeout de inactividad en segundos (5 min default)
            max_age: Edad máxima de sesión en segundos (1 hora default)
        """
        self.max_sessions = max_sessions
        self.idle_timeout = idle_timeout
        self.max_age = max_age
        
        self._pool: Dict[str, PooledSession] = {}
        self._lock = Lock()
        self.logger = get_logger()
        self.config = get_config()
    
    def get_session(self, hostname: str, creator_func):
        """
        Obtiene o crea una sesión para el host
        
        Args:
            hostname: Host para el cual obtener sesión
            creator_func: Función que crea una nueva sesión
            
        Returns:
            Sesión activa para el host
        """
        with self._lock:
            # Limpiar sesiones expiradas
            self._cleanup_expired()
            
            # Buscar sesión existente
            if hostname in self._pool:
                pooled = self._pool[hostname]
                
                # Verificar si la sesión es válida
                if self._is_session_valid(pooled):
                    pooled.mark_used()
                    self.logger.debug(f"Reutilizando sesión para {hostname} (uso #{pooled.use_count})")
                    return pooled.session
                else:
                    # Sesión expirada, eliminar
                    self._remove_session(hostname)
            
            # Crear nueva sesión
            if len(self._pool) >= self.max_sessions:
                # Pool lleno, eliminar sesión más antigua
                self._evict_oldest()
            
            try:
                session = creator_func()
                pooled = PooledSession(hostname=hostname, session=session)
                self._pool[hostname] = pooled
                
                self.logger.info(f"Nueva sesión creada para {hostname}")
                return session
                
            except Exception as e:
                self.logger.error(f"Error creando sesión para {hostname}: {e}")
                raise
    
    def release_session(self, hostname: str):
        """
        Libera una sesión (marca como disponible, no la cierra)
        
        Args:
            hostname: Host cuya sesión liberar
        """
        # En este pool simple, no hacemos nada
        # La sesión permanece en el pool para reutilización
        pass
    
    def close_session(self, hostname: str):
        """
        Cierra y elimina una sesión del pool
        
        Args:
            hostname: Host cuya sesión cerrar
        """
        with self._lock:
            self._remove_session(hostname)
    
    def close_all(self):
        """Cierra todas las sesiones del pool"""
        with self._lock:
            hostnames = list(self._pool.keys())
            for hostname in hostnames:
                self._remove_session(hostname)
            
            self.logger.info(f"Pool cerrado: {len(hostnames)} sesiones eliminadas")
    
    def _is_session_valid(self, pooled: PooledSession) -> bool:
        """Verifica si una sesión es válida"""
        if not pooled.is_active:
            return False
        
        # Verificar timeout de inactividad
        if pooled.idle_time > self.idle_timeout:
            self.logger.debug(f"Sesión expirada por inactividad: {pooled.hostname}")
            return False
        
        # Verificar edad máxima
        if pooled.age > self.max_age:
            self.logger.debug(f"Sesión expirada por edad: {pooled.hostname}")
            return False
        
        return True
    
    def _cleanup_expired(self):
        """Limpia sesiones expiradas"""
        expired = [
            hostname for hostname, pooled in self._pool.items()
            if not self._is_session_valid(pooled)
        ]
        
        for hostname in expired:
            self._remove_session(hostname)
    
    def _evict_oldest(self):
        """Elimina la sesión más antigua del pool"""
        if not self._pool:
            return
        
        # Encontrar sesión menos usada recientemente
        oldest_hostname = min(
            self._pool.keys(),
            key=lambda h: self._pool[h].last_used
        )
        
        self.logger.info(f"Evicting session: {oldest_hostname} (pool full)")
        self._remove_session(oldest_hostname)
    
    def _remove_session(self, hostname: str):
        """Elimina una sesión del pool"""
        if hostname in self._pool:
            pooled = self._pool[hostname]
            pooled.is_active = False
            
            # Intentar cerrar la sesión si tiene método close
            try:
                if hasattr(pooled.session, 'close'):
                    pooled.session.close()
            except Exception as e:
                self.logger.warning(f"Error cerrando sesión {hostname}: {e}")
            
            del self._pool[hostname]
    
    def get_stats(self) -> Dict:
        """
        Retorna estadísticas del pool
        
        Returns:
            Dict con estadísticas
        """
        with self._lock:
            total_uses = sum(p.use_count for p in self._pool.values())
            
            return {
                "active_sessions": len(self._pool),
                "max_sessions": self.max_sessions,
                "total_uses": total_uses,
                "idle_timeout": self.idle_timeout,
                "max_age": self.max_age,
                "sessions": {
                    hostname: {
                        "use_count": p.use_count,
                        "idle_time": round(p.idle_time, 1),
                        "age": round(p.age, 1)
                    }
                    for hostname, p in self._pool.items()
                }
            }
    
    def __enter__(self):
        """Context manager enter"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cierra todas las sesiones"""
        self.close_all()


# Instancia global de pool (singleton)
_pool_instance: Optional[SessionPool] = None


def get_session_pool() -> SessionPool:
    """
    Obtiene la instancia global del pool (singleton)
    
    Returns:
        SessionPool: Instancia del pool
    """
    global _pool_instance
    if _pool_instance is None:
        _pool_instance = SessionPool()
    return _pool_instance

