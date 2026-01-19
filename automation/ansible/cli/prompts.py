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
    
    Si existe el archivo .vault_pass, ofrece usarlo automáticamente.
    
    Returns:
        str: La password ingresada o None si cancela/omite
    """
    from pathlib import Path
    from .config import BASE_DIR
    
    vault_pass_file = BASE_DIR / ".vault_pass"
    
    # Si existe .vault_pass, ofrecer usarlo automáticamente
    if vault_pass_file.exists():
        console.print("\n[green]✓ Archivo .vault_pass detectado[/green]")
        console.print("[dim]Presiona Enter para usar la contraseña guardada, o escribe una nueva.[/dim]\n")
        
        password = questionary.password(
            "Vault Password (Enter = usar .vault_pass):",
            style=CUSTOM_STYLE
        ).ask()
        
        if password is None or password.strip() == "":
            # Usar la contraseña del archivo
            try:
                vault_password = vault_pass_file.read_text().strip()
                if vault_password:
                    console.print("[green]✓ Usando contraseña de .vault_pass[/green]\n")
                    return vault_password
            except Exception as e:
                console.print(f"[yellow]⚠ No se pudo leer .vault_pass: {e}[/yellow]")
        else:
            return password
    else:
        console.print("\n[dim]Si usas Ansible Vault, ingresa la master password.[/dim]")
        console.print("[dim]Presiona Enter para omitir (modo desarrollo).[/dim]\n")
        
        password = questionary.password(
            "Vault Password (opcional):",
            style=CUSTOM_STYLE
        ).ask()
        
        if password is None or password.strip() == "":
            return None
        
        return password
    
    return None


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
