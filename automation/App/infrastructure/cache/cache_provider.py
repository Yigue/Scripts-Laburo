"""
CacheProvider - Sistema de cache en memoria con TTL
"""
import time
from typing import Optional, Any, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
from domain.interfaces import ICacheProvider
from config import get_config


@dataclass
class CacheEntry:
    """Entrada de cache con TTL"""
    value: Any
    expires_at: float  # timestamp
    
    @property
    def is_expired(self) -> bool:
        """Verifica si la entrada expiró"""
        return time.time() > self.expires_at


class CacheProvider(ICacheProvider):
    """
    Proveedor de cache en memoria
    Implementa ICacheProvider interface
    """
    
    def __init__(self):
        """Inicializa el cache"""
        self.config = get_config()
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del cache
        
        Args:
            key: Clave a buscar
            
        Returns:
            Valor almacenado o None si no existe/expiró
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        
        # Verificar si expiró
        if entry.is_expired:
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: int = None):
        """
        Almacena un valor en el cache
        
        Args:
            key: Clave
            value: Valor a almacenar
            ttl: Time-to-live en segundos (usa default si no se especifica)
        """
        if not self.config.cache_enabled:
            return
        
        if ttl is None:
            ttl = self.config.cache_ttl_default
        
        expires_at = time.time() + ttl
        
        self._cache[key] = CacheEntry(
            value=value,
            expires_at=expires_at
        )
    
    def invalidate(self, key: str):
        """
        Invalida/elimina una entrada del cache
        
        Args:
            key: Clave a invalidar
        """
        if key in self._cache:
            del self._cache[key]
    
    def clear_all(self):
        """Limpia todo el cache"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def clear_expired(self):
        """Elimina entradas expiradas"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del self._cache[key]
    
    @property
    def size(self) -> int:
        """Retorna número de entradas en cache"""
        return len(self._cache)
    
    @property
    def hit_rate(self) -> float:
        """Retorna tasa de aciertos"""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return (self._hits / total) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del cache"""
        return {
            "size": self.size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
            "enabled": self.config.cache_enabled
        }


# Instancia global de cache
_cache_instance: Optional[CacheProvider] = None


def get_cache() -> CacheProvider:
    """
    Obtiene la instancia global del cache (singleton)
    
    Returns:
        CacheProvider: Instancia del cache
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheProvider()
    return _cache_instance

