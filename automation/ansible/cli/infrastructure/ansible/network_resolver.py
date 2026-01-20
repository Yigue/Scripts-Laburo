# -*- coding: utf-8 -*-
"""
infrastructure/ansible/network_resolver.py
=========================================
Resolución de red y DNS.

Contiene funciones para resolver hostnames, detectar WSL gateway y probar conectividad.
"""

import subprocess
import socket
from typing import Optional, Tuple

import logging

logger = logging.getLogger(__name__)


def get_wsl_gateway() -> Optional[str]:
    """
    Obtiene la IP del gateway de WSL (Windows host).
    
    Returns:
        IP del gateway o None si no se puede obtener
    """
    try:
        result = subprocess.check_output(
            "ip route show | grep default | awk '{print $3}'",
            shell=True, stderr=subprocess.DEVNULL
        ).decode().strip()
        return result if result else None
    except Exception:
        return None


def resolve_hostname(hostname: str) -> Tuple[Optional[str], str]:
    """
    Intenta resolver un hostname a una IP válida.
    
    Detecta si el hostname resuelve a localhost (problema común en WSL)
    y sugiere alternativas.
    
    Args:
        hostname: El hostname a resolver
        
    Returns:
        Tuple (ip, mensaje): IP resuelta o None, y mensaje descriptivo
    """
    # Si ya es una IP, retornarla
    try:
        socket.inet_aton(hostname)
        return hostname, "Es una IP válida"
    except socket.error:
        pass
    
    # Intentar resolver con socket
    try:
        result = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if result:
            ip = result[0][4][0]
            # Verificar que no sea localhost
            if ip.startswith("127.") or ip == "::1":
                return None, f"DNS resuelve a localhost ({ip})"
            return ip, f"Resuelto vía DNS a {ip}"
    except socket.gaierror:
        pass
    
    return None, "No se pudo resolver el hostname"


def test_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """
    Verifica si un puerto está abierto en un host.
    
    Args:
        host: IP o hostname del host
        port: Puerto a verificar
        timeout: Timeout en segundos
        
    Returns:
        True si el puerto está abierto, False en caso contrario
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False
