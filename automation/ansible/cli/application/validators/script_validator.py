# -*- coding: utf-8 -*-
"""
application/validators/script_validator.py
==========================================
Validador de scripts PowerShell.

Contiene funciones para validar scripts PowerShell antes de ejecutarlos remotamente.
"""

import re
from typing import Optional
import questionary

from ...shared.config import console, CUSTOM_STYLE


def validate_powershell_script(script: str) -> Optional[str]:
    """
    Valida un script PowerShell antes de ejecutarlo remotamente.
    
    Args:
        script: El script a validar
        
    Returns:
        El script validado, o None si el usuario cancela después de advertencia
    """
    if not script or not script.strip():
        console.print("[red]❌ El script no puede estar vacío[/red]")
        return None
    
    # Validar longitud máxima (prevenir scripts excesivamente largos)
    if len(script) > 10000:
        console.print("[red]❌ El script es demasiado largo (máximo 10000 caracteres)[/red]")
        return None
    
    # Lista de comandos/comandos peligrosos (bloqueados)
    comandos_peligrosos = [
        r'\bFormat-Volume\b',
        r'\bRemove-Item\s+-Recurse\s+-Force\s+C:\\',
        r'\bInvoke-Expression\s*\(\s*[^\)]*Get-Content\s+[^\)]*\)',
        r'\bStart-Process\s+-FilePath\s+["\']?C:\\Windows\\System32\\shutdown',
        r'\bStop-Computer\s+-Force',
        r'\bRestart-Computer\s+-Force',
        r'\bClear-EventLog',
        r'\bRemove-EventLog',
    ]
    
    # Detectar comandos peligrosos
    for pattern in comandos_peligrosos:
        if re.search(pattern, script, re.IGNORECASE):
            console.print("[yellow]⚠ ADVERTENCIA: Se detectó un comando potencialmente peligroso[/yellow]")
            console.print("[dim]Comando detectado que podría:[/dim]")
            console.print("[dim]  - Formatear discos[/dim]")
            console.print("[dim]  - Eliminar archivos del sistema[/dim]")
            console.print("[dim]  - Apagar/reiniciar el equipo[/dim]")
            console.print("[dim]  - Modificar logs del sistema[/dim]")
            
            confirmar = questionary.confirm(
                "¿Estás seguro de que quieres ejecutar este script?",
                style=CUSTOM_STYLE,
                default=False
            ).ask()
            
            if not confirmar:
                console.print("[yellow]Operación cancelada por seguridad[/yellow]")
                return None
    
    # Detectar patrones sospechosos (no bloquear, solo advertir)
    patrones_sospechosos = [
        (r'\bSet-ExecutionPolicy\s+-Bypass', "Cambiar política de ejecución"),
        (r'\bSet-ExecutionPolicy\s+-Unrestricted', "Desactivar restricciones de ejecución"),
        (r'\bInvoke-WebRequest\s+-Uri\s+http', "Descargar contenido de Internet"),
        (r'\bIEX\s*\(', "Invoke-Expression (abreviatura)"),
        (r'\b.\s*\(', "Llamadas a métodos sospechosas"),
    ]
    
    advertencias = []
    for pattern, descripcion in patrones_sospechosos:
        if re.search(pattern, script, re.IGNORECASE):
            advertencias.append(descripcion)
    
    if advertencias:
        console.print("[yellow]⚠ ADVERTENCIA: Se detectaron patrones sospechosos:[/yellow]")
        for adv in advertencias:
            console.print(f"[dim]  - {adv}[/dim]")
        
        confirmar = questionary.confirm(
            "¿Continuar con la ejecución?",
            style=CUSTOM_STYLE,
            default=False
        ).ask()
        
        if not confirmar:
            console.print("[yellow]Operación cancelada[/yellow]")
            return None
    
    return script
