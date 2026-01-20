# -*- coding: utf-8 -*-
"""
infrastructure/ansible/vault_manager.py
======================================
Gestor de Vault de Ansible.

Contiene funciones para descifrar variables del vault de Ansible.
"""

import os
import subprocess
import tempfile
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict

from ...shared.config import BASE_DIR, logger
from ...shared.exceptions import VaultDecryptionError
from ...infrastructure.logging.debug_logger import debug_logger


def decrypt_vault(vault_password: Optional[str] = None) -> Dict[str, str]:
    """
    Descifra el archivo vault.yml y retorna un diccionario con las variables.
    
    Args:
        vault_password: Password del vault (opcional)
        
    Returns:
        Dict con las variables del vault (vault_ansible_user, vault_ansible_password, etc.)
        o diccionario vacío si no se puede descifrar
    """
    if not vault_password:
        return {}
    
    vault_file = BASE_DIR / "inventory" / "group_vars" / "all" / "vault.yml"
    if not vault_file.exists():
        logger.warning("Archivo vault.yml no encontrado")
        return {}
    
    try:
        # Usar ansible-vault view para leer contenido descifrado
        vault_pass_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        vault_pass_file.write(vault_password)
        vault_pass_file.close()
        
        cmd = [
            "ansible-vault",
            "view",
            "--vault-password-file", vault_pass_file.name,
            str(vault_file)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(BASE_DIR)
        )
        
        # Limpiar archivo temporal de password
        if os.path.exists(vault_pass_file.name):
            os.unlink(vault_pass_file.name)
        
        if result.returncode != 0:
            logger.warning(f"No se pudo descifrar vault: {result.stderr}")
            debug_logger.log(
                "infrastructure/ansible/vault_manager.py:47",
                "Error descifrando vault",
                {"returncode": result.returncode, "stderr": result.stderr[:200]},
                hypothesis_id="E"
            )
            return {}
        
        # Verificar si el output está vacío o solo tiene whitespace
        if not result.stdout or not result.stdout.strip():
            logger.warning("Vault descifrado está vacío - no hay variables definidas")
            debug_logger.log(
                "infrastructure/ansible/vault_manager.py:56",
                "Vault vacío",
                {"stdout_length": len(result.stdout) if result.stdout else 0},
                hypothesis_id="E"
            )
            return {}
        
        # Parsear YAML del output
        try:
            vault_vars = yaml.safe_load(result.stdout)
            debug_logger.log(
                "infrastructure/ansible/vault_manager.py:65",
                "Vault descifrado",
                {
                    "has_vars": vault_vars is not None,
                    "keys": list(vault_vars.keys()) if vault_vars else [],
                    "has_user": "vault_ansible_user" in (vault_vars or {}),
                    "has_password": "vault_ansible_password" in (vault_vars or {}),
                    "stdout_preview": result.stdout[:200]
                },
                hypothesis_id="E"
            )
            if vault_vars and isinstance(vault_vars, dict):
                return vault_vars
        except Exception as e:
            logger.warning(f"Error parseando vault YAML: {e}")
            debug_logger.log(
                "infrastructure/ansible/vault_manager.py:77",
                "Error parseando vault YAML",
                {"error": str(e), "stdout_preview": result.stdout[:200] if result.stdout else None},
                hypothesis_id="E"
            )
            return {}
            
    except Exception as e:
        logger.error(f"Error descifrando vault: {e}")
        debug_logger.log(
            "infrastructure/ansible/vault_manager.py:84",
            "Excepción en descifrado vault",
            {"error_type": type(e).__name__, "error_msg": str(e)},
            hypothesis_id="E"
        )
        return {}
    
    return {}
