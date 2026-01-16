# -*- coding: utf-8 -*-
"""
cli/prompts.py
==============
Funciones de entrada de usuario mejoradas.
"""

from typing import Optional, List
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
    
    return result if result is not None else False


def solicitar_targets() -> Optional[List[str]]:
    """
    Solicita uno o más hostnames al usuario.
    
    Returns:
        List[str]: Lista de hostnames (en mayúsculas) o None si cancela
    """
    # Preguntar si quiere ejecutar en uno o múltiples equipos
    mode_choice = questionary.select(
        "¿En cuántos equipos deseas ejecutar?",
        choices=[
            "Un solo equipo",
            "Múltiples equipos"
        ],
        style=CUSTOM_STYLE,
        use_shortcuts=True
    ).ask()
    
    if mode_choice is None:
        return None
    
    if "Un solo equipo" in mode_choice:
        # Solo un equipo
        hostname = solicitar_hostname()
        return [hostname] if hostname else None
    else:
        # Múltiples equipos
        console.print("\n[dim]Ingresa los hostnames separados por comas, espacios o uno por línea.[/dim]")
        console.print("[dim]Presiona Enter en una línea vacía para terminar.[/dim]\n")
        
        targets_input = questionary.text(
            "Hostnames (separados por comas o espacios):",
            style=CUSTOM_STYLE
        ).ask()
        
        if targets_input is None or not targets_input.strip():
            return None
        
        # Parsear hostnames (soporta comas, espacios, y múltiples líneas)
        targets = []
        for line in targets_input.split('\n'):
            # Separar por comas y espacios
            line_targets = [t.strip().upper() for t in line.replace(',', ' ').split() if t.strip()]
            targets.extend(line_targets)
        
        # Eliminar duplicados manteniendo orden
        seen = set()
        unique_targets = []
        for target in targets:
            if target not in seen:
                seen.add(target)
                unique_targets.append(target)
        
        if not unique_targets:
            console.print("[yellow]No se ingresaron hostnames válidos[/yellow]")
            return None
        
        console.print(f"\n[green]Se ejecutará en {len(unique_targets)} equipo(s):[/green]")
        for target in unique_targets:
            console.print(f"  • {target}")
        
        confirm = questionary.confirm(
            "¿Continuar?",
            style=CUSTOM_STYLE,
            default=True
        ).ask()
        
        return unique_targets if confirm else None
