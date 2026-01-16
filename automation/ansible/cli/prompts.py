# -*- coding: utf-8 -*-
"""
cli/prompts.py
==============
Funciones de entrada de usuario.

Contiene:
- solicitar_hostname(): Pide el hostname al usuario
- solicitar_vault_password(): Pide la password del vault
- interactive_confirm(): Confirmación rápida sí/no
"""

from typing import Optional
import questionary

from .config import console, CUSTOM_STYLE


def solicitar_hostname() -> Optional[str]:
    """
    Solicita el hostname al usuario usando Questionary.
    
    Returns:
        str: El hostname ingresado (en mayúsculas) o None si cancela
    """
    hostname = questionary.text(
        "Ingrese el hostname del equipo:",
        style=CUSTOM_STYLE,
        validate=lambda text: len(text.strip()) > 0 or "Debe ingresar un hostname"
    ).ask()
    
    if hostname is None:
        return None
    
    return hostname.strip().upper()


def solicitar_vault_password() -> Optional[str]:
    """
    Solicita la master password del Ansible Vault.
    
    Returns:
        str: La password ingresada o None si cancela/omite
    """
    console.print("\n[dim]Si usas Ansible Vault, ingresa la master password.[/dim]")
    console.print("[dim]Presiona Enter para omitir (modo desarrollo).[/dim]\n")
    
    password = questionary.password(
        "Vault Password (opcional):",
        style=CUSTOM_STYLE
    ).ask()
    
    if password is None or password.strip() == "":
        return None
    
    return password


def interactive_confirm(message: str, default: bool = True) -> bool:
    """
    Helper para confirmación rápida sí/no.
    
    Args:
        message: Mensaje a mostrar
        default: Valor por defecto si presiona Enter
        
    Returns:
        bool: True si confirma, False si no
    """
    result = questionary.confirm(
        message,
        style=CUSTOM_STYLE,
        default=default
    ).ask()
    
    # Si es None (cancelado), retornar False
    return result if result is not None else False
