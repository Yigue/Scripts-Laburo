# -*- coding: utf-8 -*-
"""
cli/menus.py
============
Funciones de navegación de menú.

Contiene:
- mostrar_menu_categorias(): Muestra y selecciona categoría
- mostrar_menu_opciones(): Muestra opciones de una categoría
- ejecutar_opcion(): Ejecuta una opción del menú
"""

from typing import Optional
import questionary

from .config import console, CUSTOM_STYLE
from .models import MenuOption, MenuCategory
from .menu_data import MENU_CATEGORIES
from .ansible_runner import ejecutar_playbook
from .display import (
    mostrar_resultado, mostrar_specs_tabla, 
    mostrar_laps_resultado, mostrar_bitlocker_resultado,
    mostrar_updates_resultado, mostrar_bitlocker_status_tabla,
    mostrar_ad_info, mostrar_audit_groups_resultado,
    mostrar_auditoria_salud, guardar_reporte,
    mostrar_dashboard_ejecucion, mostrar_historial_sesion
)
from .history import session_history


def mostrar_menu_categorias() -> Optional[MenuCategory]:
    """
    Muestra el menú de categorías y retorna la seleccionada.
    
    Returns:
        MenuCategory: La categoría seleccionada, o None si cancela/sale
    """
    choices = []
    for cat in MENU_CATEGORIES:
        choices.append(f"{cat.icon} [{cat.key}] {cat.name} ({len(cat.options)} opciones)")
    
    choices.append("───────────────────")
    choices.append("📜 [H] Ver Historial de Sesión")
    choices.append("🔄 [0] Cambiar equipo")
    choices.append("❌ [X] Salir")
    
    answer = questionary.select(
        "Seleccione una categoría:",
        choices=choices,
        style=CUSTOM_STYLE,
        use_shortcuts=True # Habilita navegación por números 1-9
    ).ask()
    
    if answer is None or "Salir" in answer:
        return None
    
    if "Ver Historial" in answer:
        mostrar_historial_sesion(session_history.get_entries())
        questionary.press_any_key_to_continue("Presione cualquier tecla para volver...").ask()
        return MenuCategory(key="H", name="Historial", icon="", options=[])

    if "Cambiar equipo" in answer:
        return MenuCategory(key="0", name="Cambiar", icon="", options=[])
    
    # Buscar categoría seleccionada
    for cat in MENU_CATEGORIES:
        if f"[{cat.key}]" in answer:
            return cat
    
    return None


def mostrar_menu_opciones(categoria: MenuCategory) -> Optional[MenuOption]:
    """
    Muestra las opciones de una categoría y retorna la seleccionada.
    
    Args:
        categoria: La categoría cuyas opciones mostrar
        
    Returns:
        MenuOption: La opción seleccionada, o None si vuelve atrás
    """
    choices = []
    for opt in categoria.options:
        choices.append(f"[{opt.key}] {opt.label}")
    
    choices.append("───────────────────")
    choices.append("⬅️  Volver")
    
    answer = questionary.select(
        f"{categoria.icon} {categoria.name}:",
        choices=choices,
        style=CUSTOM_STYLE,
        use_shortcuts=True
    ).ask()
    
    if answer is None or "Volver" in answer:
        return None
    
    # Buscar opción seleccionada
    for opt in categoria.options:
        if f"[{opt.key}]" in answer:
            return opt
    
    return None


def ejecutar_opcion(
    opcion: MenuOption,
    hostname: str,
    vault_password: Optional[str] = None
):
    """
    Ejecuta una opción del menú.
    
    Muestra información de la opción, solicita input adicional si es
    necesario, pide confirmación, ejecuta el playbook y muestra resultados.
    
    Args:
        opcion: La opción de menú a ejecutar
        hostname: Hostname del equipo destino
        vault_password: Password del vault (opcional)
    """
    console.print(f"\n[cyan]▶ Ejecutando: {opcion.label}[/cyan]")
    console.print(f"[dim]{opcion.description}[/dim]\n")
    
    extra_vars = {}
    
    # Si la opción requiere input adicional
    if opcion.requires_input:
        user_input = questionary.text(
            opcion.input_prompt + ":",
            style=CUSTOM_STYLE
        ).ask()
        
        if user_input is None:
            console.print("[yellow]Operación cancelada[/yellow]")
            return
        
        var_name = opcion.input_var_name if opcion.input_var_name else "user_input"
        extra_vars[var_name] = user_input
    
    # Confirmar ejecución
    confirm = questionary.confirm(
        f"¿Ejecutar '{opcion.label}' en {hostname}?",
        style=CUSTOM_STYLE,
        default=True
    ).ask()
    
    if not confirm:
        console.print("[yellow]Operación cancelada[/yellow]")
        return
    
    # Detectar si es una tarea interactiva (ej. consola remota)
    es_interactiva = (opcion.key == "C1")
    
    # Ejecutar playbook
    result = ejecutar_playbook(
        hostname=hostname,
        playbook_path=opcion.playbook,
        vault_password=vault_password,
        extra_vars=extra_vars if extra_vars else None,
        interactive=es_interactiva
    )
    
    # Guardar en el historial
    session_history.add_entry(hostname, opcion.label, result)

    # Mostrar resultados según el tipo de opción
    if not es_interactiva:
        if opcion.key == "H1":  # Specs
            mostrar_specs_tabla(result, hostname)
        elif opcion.key == "A2":  # LAPS
            mostrar_laps_resultado(result, hostname)
        elif opcion.key == "A3":  # BitLocker Key
            mostrar_bitlocker_resultado(result, hostname)
        elif opcion.key == "H9":  # Windows Updates
            mostrar_updates_resultado(result, hostname)
        elif opcion.key == "A5":  # BitLocker Status
            mostrar_bitlocker_status_tabla(result, hostname)
        elif opcion.key == "A4":  # AD Info
            mostrar_ad_info(result, hostname)
        elif opcion.key == "A6":  # AD Groups
            mostrar_audit_groups_resultado(result, hostname)
        elif opcion.key == "H10":  # Health Audit Combo
            mostrar_auditoria_salud(result, hostname)
        else:
            mostrar_resultado(result, opcion.label)
        
        # Opción de guardar reporte para tareas clave
        if opcion.key in ["H1", "H7", "H8", "H9", "H10", "A4", "A6"]:
            if questionary.confirm("¿Deseas guardar este resultado como un reporte HTML?", default=False).ask():
                guardar_reporte(hostname)
    else:
        console.print(f"\n[green]✅ Tarea interactiva finalizada[/green]")
    
    # Esperar antes de volver al menú
    console.print("")
    questionary.press_any_key_to_continue(
        "Presione cualquier tecla para continuar..."
    ).ask()
