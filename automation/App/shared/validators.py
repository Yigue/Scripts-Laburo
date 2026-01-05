"""
Validadores de input para la aplicación
Funciones para validar hostnames, IPs, paths, etc.
"""
import re
import os
from pathlib import Path
from typing import Optional
from .constants import HOSTNAME_PATTERN, IP_PATTERN, MAC_PATTERN
from .exceptions import ValidationError


def validate_hostname(hostname: str, raise_on_invalid: bool = False) -> bool:
    """
    Valida formato de hostname (ej: NB001234, PC005678)
    
    Args:
        hostname: Nombre del host a validar
        raise_on_invalid: Si True, lanza ValidationError en lugar de retornar False
        
    Returns:
        bool: True si es válido, False si no lo es
        
    Raises:
        ValidationError: Si raise_on_invalid=True y el hostname es inválido
    """
    if not hostname or not isinstance(hostname, str):
        if raise_on_invalid:
            raise ValidationError(f"Hostname inválido: {hostname}")
        return False
    
    is_valid = bool(re.match(HOSTNAME_PATTERN, hostname, re.IGNORECASE))
    
    if not is_valid and raise_on_invalid:
        raise ValidationError(f"Hostname no cumple formato esperado: {hostname}")
    
    return is_valid


def validate_ip_address(ip: str, raise_on_invalid: bool = False) -> bool:
    """
    Valida formato de dirección IP
    
    Args:
        ip: Dirección IP a validar
        raise_on_invalid: Si True, lanza ValidationError
        
    Returns:
        bool: True si es válido
    """
    if not ip or not isinstance(ip, str):
        if raise_on_invalid:
            raise ValidationError(f"IP inválida: {ip}")
        return False
    
    is_valid = bool(re.match(IP_PATTERN, ip))
    
    # Validar rangos (0-255)
    if is_valid:
        octets = ip.split('.')
        is_valid = all(0 <= int(octet) <= 255 for octet in octets)
    
    if not is_valid and raise_on_invalid:
        raise ValidationError(f"Dirección IP inválida: {ip}")
    
    return is_valid


def validate_mac_address(mac: str, raise_on_invalid: bool = False) -> bool:
    """Valida formato de dirección MAC"""
    if not mac or not isinstance(mac, str):
        if raise_on_invalid:
            raise ValidationError(f"MAC inválida: {mac}")
        return False
    
    is_valid = bool(re.match(MAC_PATTERN, mac))
    
    if not is_valid and raise_on_invalid:
        raise ValidationError(f"Dirección MAC inválida: {mac}")
    
    return is_valid


def validate_path(path: str, must_exist: bool = False, raise_on_invalid: bool = False) -> bool:
    """
    Valida path de archivo o directorio
    
    Args:
        path: Path a validar
        must_exist: Si True, verifica que el path exista
        raise_on_invalid: Si True, lanza ValidationError
        
    Returns:
        bool: True si es válido
    """
    if not path or not isinstance(path, str):
        if raise_on_invalid:
            raise ValidationError(f"Path inválido: {path}")
        return False
    
    try:
        p = Path(path)
        
        if must_exist and not p.exists():
            if raise_on_invalid:
                raise ValidationError(f"Path no existe: {path}")
            return False
        
        return True
    except Exception as e:
        if raise_on_invalid:
            raise ValidationError(f"Path inválido: {path}. Error: {e}")
        return False


def validate_port(port: int, raise_on_invalid: bool = False) -> bool:
    """Valida número de puerto (1-65535)"""
    if not isinstance(port, int) or port < 1 or port > 65535:
        if raise_on_invalid:
            raise ValidationError(f"Puerto inválido: {port}")
        return False
    return True


def validate_timeout(timeout: int, min_value: int = 1, max_value: int = 3600, raise_on_invalid: bool = False) -> bool:
    """
    Valida valor de timeout
    
    Args:
        timeout: Valor de timeout en segundos
        min_value: Valor mínimo permitido
        max_value: Valor máximo permitido
        raise_on_invalid: Si True, lanza ValidationError
    """
    if not isinstance(timeout, int) or timeout < min_value or timeout > max_value:
        if raise_on_invalid:
            raise ValidationError(f"Timeout inválido: {timeout}. Debe estar entre {min_value} y {max_value}")
        return False
    return True


def validate_not_empty(value: Optional[str], field_name: str = "Campo", raise_on_invalid: bool = False) -> bool:
    """Valida que un string no esté vacío"""
    if not value or not value.strip():
        if raise_on_invalid:
            raise ValidationError(f"{field_name} no puede estar vacío")
        return False
    return True

