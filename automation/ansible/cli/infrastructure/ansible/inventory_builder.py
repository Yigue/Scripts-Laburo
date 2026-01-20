# -*- coding: utf-8 -*-
"""
infrastructure/ansible/inventory_builder.py
==========================================
Constructor de inventarios dinámicos de Ansible.

Construye inventarios dinámicos en formato INI para conectar a hosts sin necesidad
de tenerlos en el inventario estático.
"""

import socket
from pathlib import Path
from typing import Optional, Dict
import logging

from ...shared.config import BASE_DIR, logger
from ..ansible.network_resolver import get_wsl_gateway, resolve_hostname, test_port
from ...infrastructure.logging.debug_logger import debug_logger


# Variables por defecto de WinRM para inventario dinámico
DEFAULT_WINRM_VARS = {
    "ansible_connection": "winrm",
    "ansible_winrm_transport": "ntlm",
    "ansible_winrm_scheme": "http",
    "ansible_port": "5985",
    "ansible_winrm_server_cert_validation": "ignore",
    "ansible_shell_type": "powershell",
    "ansible_user": "{{ vault_ansible_user }}",
    "ansible_password": "{{ vault_ansible_password }}",
}


def ensure_cache_setup() -> Path:
    """
    Prepara el directorio .cache y asegura que group_vars esté accessible.
    
    Esto es necesario porque al usar un inventario temporal en .cache/,
    Ansible busca group_vars en .cache/group_vars por defecto.
    
    Returns:
        Path del directorio de cache
    """
    cache_dir = BASE_DIR / ".cache"
    cache_dir.mkdir(exist_ok=True)
    
    # Symlink de group_vars para que cargue variables del vault/inventario
    src_vars = BASE_DIR / "inventory" / "group_vars"
    dst_vars = cache_dir / "group_vars"
    
    if src_vars.exists():
        try:
            # Si no existe ni es link, crear
            if not dst_vars.exists() and not dst_vars.is_symlink():
                dst_vars.symlink_to(src_vars)
            # Si es link pero está roto (exists() -> False), recrear
            elif dst_vars.is_symlink() and not dst_vars.exists():
                dst_vars.unlink()
                dst_vars.symlink_to(src_vars)
        except Exception as e:
            logger.warning(f"No se pudo configurar symlink de group_vars: {e}")
            
    return cache_dir


def build_dynamic_inventory(
    hostname: str, 
    resolved_ip: Optional[str] = None,
    vault_vars: Optional[Dict[str, str]] = None
) -> str:
    """
    Construye un inventario dinámico en formato INI para un host.
    
    Este inventario permite conectarse a cualquier hostname sin
    necesidad de tenerlo en el archivo hosts.ini estático.
    
    Si resolved_ip está disponible, usa ansible_host para dirigir
    la conexión a esa IP en lugar de depender del DNS local.
    
    Args:
        hostname: El hostname o IP del equipo
        resolved_ip: IP resuelta (opcional, para evitar problemas DNS)
        vault_vars: Variables del vault descifradas (opcional)
        
    Returns:
        str: Contenido del inventario en formato INI
    """
    # Si no tenemos IP resuelta, intentar resolver
    if not resolved_ip:
        # TRUCO: Si el hostname ingresado es el de tu propia máquina, 
        # forzamos el uso de la IP del Gateway de WSL automáticamente.
        my_hostname = socket.gethostname().lower()
        if hostname.lower() in [my_hostname, "localhost", "127.0.0.1", "127.0.1.1"]:
            gateway = get_wsl_gateway()
            if gateway:
                resolved_ip = gateway
                logger.info(f"Target es local, forzando IP de Gateway: {gateway}")
        
        # Si aún no hay IP, intentar resolver normalmente
        if not resolved_ip:
            resolved_ip, msg = resolve_hostname(hostname)
            
            # Si el DNS falla (resuelve a localhost), intentar con el gateway como último recurso
            if not resolved_ip:
                gateway = get_wsl_gateway()
                if gateway and test_port(gateway, 5985):
                    logger.info(f"DNS resuelve mal para {hostname}, usando gateway WSL: {gateway}")
                    resolved_ip = gateway
    
    lines = [
        "[target]",
        hostname,
        "",
        "[windows_hosts:children]",
        "target",
        "",
        "[target:vars]",
    ]
    
    # Agregar ansible_host si tenemos una IP válida diferente al hostname
    if resolved_ip and resolved_ip != hostname:
        lines.append(f"ansible_host={resolved_ip}")
    
    # Usar variables del vault si están disponibles, sino usar referencias {{ }} 
    # para que Ansible las cargue desde group_vars/all/vault.yml cuando se proporcione --vault-password-file
    vault_vars = vault_vars or {}
    debug_logger.log(
        "infrastructure/ansible/inventory_builder.py:95",
        "Construyendo inventario dinámico",
        {
            "has_vault_vars": bool(vault_vars),
            "vault_keys": list(vault_vars.keys()) if vault_vars else [],
            "has_user": "vault_ansible_user" in vault_vars,
            "has_password": "vault_ansible_password" in vault_vars
        },
        hypothesis_id="E"
    )
    
    has_user = "vault_ansible_user" in vault_vars
    has_password = "vault_ansible_password" in vault_vars
    
    for key, default_value in DEFAULT_WINRM_VARS.items():
        # Para ansible_user y ansible_password:
        # 1. Si tenemos valores del vault descifrados, usar los valores directamente
        # 2. Si no, usar referencias {{ }} para que Ansible las cargue desde group_vars/all/vault.yml
        if key == "ansible_user":
            if has_user:
                lines.append(f"ansible_user={vault_vars['vault_ansible_user']}")
            else:
                # Usar referencia para que Ansible la cargue del vault
                lines.append(f"ansible_user={default_value}")
        elif key == "ansible_password":
            if has_password:
                lines.append(f"ansible_password={vault_vars['vault_ansible_password']}")
            else:
                # Usar referencia para que Ansible la cargue del vault
                lines.append(f"ansible_password={default_value}")
        else:
            # Para las demás variables, siempre agregar
            lines.append(f"{key}={default_value}")
    
    inventory_content = "\n".join(lines)
    debug_logger.log(
        "infrastructure/ansible/inventory_builder.py:123",
        "Inventario dinámico generado",
        {"content": inventory_content},
        hypothesis_id="E"
    )
    return inventory_content
