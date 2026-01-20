# -*- coding: utf-8 -*-
"""
shared/exceptions.py
====================
Excepciones personalizadas de la aplicación.
"""


class AnsibleExecutionError(Exception):
    """Error durante la ejecución de un playbook de Ansible."""
    pass


class VaultDecryptionError(Exception):
    """Error al descifrar el vault de Ansible."""
    pass


class InventoryError(Exception):
    """Error al construir o procesar el inventario."""
    pass


class NetworkError(Exception):
    """Error de red o conectividad."""
    pass


class ValidationError(Exception):
    """Error de validación."""
    pass
