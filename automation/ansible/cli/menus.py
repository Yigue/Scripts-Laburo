# -*- coding: utf-8 -*-
"""
cli/menus.py
============
Funciones de navegación de menú mejoradas con ejecución en segundo plano.
"""

from typing import Optional
import questionary

from .config import console, CUSTOM_STYLE
from .models import MenuOption, MenuCategory
from .menu_data import MENU_CATEGORIES
from .ansible_runner import ejecutar_playbook
from .task_manager import (
    add_task as task_add_task,
    update_task as task_update_task,
    get_active_tasks as task_get_active_tasks
)
from .task_panel import get_task_panel
from .prompts import solicitar_targets
import uuid
from .display import (
    mostrar_resultado, mostrar_specs_tabla, 
    mostrar_laps_resultado, mostrar_bitlocker_resultado,
    mostrar_updates_resultado, mostrar_bitlocker_status_tabla,
    mostrar_ad_info, mostrar_audit_groups_resultado,
    mostrar_auditoria_salud, guardar_reporte,
    mostrar_dashboard_ejecucion, mostrar_historial_sesion
)
from .history import add_entry as history_add_entry

# Intentar importar ejecutar_playbook_nueva_ventana si existe
try:
    from .ansible_runner import ejecutar_playbook_nueva_ventana
except ImportError:
    ejecutar_playbook_nueva_ventana = None


def mostrar_menu_categorias() -> Optional[MenuCategory]:
    """
    Muestra el menú de categorías - versión minimalista.
    
    Returns:
        MenuCategory: La categoría seleccionada, o None si cancela/sale
    """
    # Preparar opciones simplificadas (sin teclas visibles)
    choices = []
    for cat in MENU_CATEGORIES:
        choices.append(f"{cat.icon} {cat.name}")
    
    choices.append(questionary.Separator())
    choices.append("Historial")
    choices.append("Dashboard")
    choices.append("Salir")
    
    answer = questionary.select(
        "Seleccione una opción:",
        choices=choices,
        style=CUSTOM_STYLE,
        use_indicator=True
    ).ask()
    
    if answer is None or "Salir" in answer:
        return None
    
    if "Historial" in answer:
        return MenuCategory(key="H", name="Historial", icon="", options=[], color="cyan")

    if "Dashboard" in answer:
        return MenuCategory(key="D", name="Dashboard", icon="", options=[], color="cyan")
    
    # Buscar categoría seleccionada por nombre
    for cat in MENU_CATEGORIES:
        if cat.name in answer or cat.icon in answer:
            return cat
    
    return None


def mostrar_menu_opciones(categoria: MenuCategory) -> Optional[MenuOption]:
    """
    Muestra las opciones de una categoría - versión minimalista.
    
    Args:
        categoria: La categoría cuyas opciones mostrar
        
    Returns:
        MenuOption: La opción seleccionada, o None si vuelve atrás
    """
    choices = []
    for opt in categoria.options:
        choices.append(opt.label)
    
    choices.append(questionary.Separator())
    choices.append("← Volver")
    
    answer = questionary.select(
        f"{categoria.icon} {categoria.name}",
        choices=choices,
        style=CUSTOM_STYLE,
        use_indicator=True
    ).ask()
    
    if answer is None or "Volver" in answer:
        return None
    
    # Buscar opción seleccionada por label
    for opt in categoria.options:
        if opt.label in answer:
            return opt
    
    return None


def ejecutar_opcion(
    opcion: MenuOption,
    hostname: Optional[str] = None,
    vault_password: Optional[str] = None
):
    """
    Ejecuta una opción del menú mejorada con soporte para segundo plano y nueva ventana.
    
    Muestra información de la opción, solicita input adicional si es necesario,
    pide confirmación y modo de ejecución, ejecuta el playbook y muestra resultados.
    Si la opción requiere hostname, lo solicita. Soporta múltiples targets.
    
    Args:
        opcion: La opción de menú a ejecutar
        hostname: Hostname del equipo destino (opcional, se solicita si requires_hostname=True)
        vault_password: Password del vault (opcional)
    """
    console.print(f"\n[cyan]▶ Ejecutando: {opcion.label}[/cyan]")
    console.print(f"[dim]{opcion.description}[/dim]\n")
    
    # Si la opción requiere hostname, solicitarlo (o múltiples targets)
    targets = []
    if opcion.requires_hostname:
        if hostname is None:
            # Solicitar targets (1 o múltiples)
            targets_input = solicitar_targets()
            if targets_input is None:
                console.print("[yellow]Operación cancelada[/yellow]")
                return
            targets = targets_input
        else:
            targets = [hostname]
    else:
        # No requiere hostname (p. ej. AD unlock solo necesita username)
        targets = [""]  # Target vacío para opciones que no requieren hostname
    
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
    
    # Confirmar ejecución (excepto read-only sin confirmación)
    if opcion.action_type != "read-only":
        target_str = f" en {', '.join(targets)}" if targets and targets[0] else ""
        confirm = questionary.confirm(
            f"¿Ejecutar '{opcion.label}'{target_str}?",
            style=CUSTOM_STYLE,
            default=True
        ).ask()
        
        if not confirm:
            console.print("[yellow]Operación cancelada[/yellow]")
            return
    
    # Seleccionar modo de ejecución si está disponible
    execution_mode = "normal"  # normal, background, new_window
    
    if ejecutar_playbook_nueva_ventana and opcion.can_new_window and opcion.key == "C1":  # Consola remota
        execution_mode = "new_window"
        console.print("[cyan]ℹ Se abrirá en una nueva ventana para interacción directa[/cyan]\n")
    elif opcion.can_background and opcion.action_type == "read-only":
        # Para read-only, preguntar si quiere ejecutar en segundo plano
        mode_choice = questionary.select(
            "¿Cómo deseas ejecutar esta tarea?",
            choices=[
                "Ejecutar normalmente (ver resultado inmediato)",
                "Ejecutar en segundo plano (continuar trabajando)"
            ],
            style=CUSTOM_STYLE,
            use_shortcuts=True
        ).ask()
        
        if mode_choice and "segundo plano" in mode_choice:
            execution_mode = "background"
    
    # Si hay múltiples targets, siempre ejecutar en background
    if len(targets) > 1:
        execution_mode = "background"
    
    # Ejecutar para cada target
    results = []
    for target_host in targets:
        # Crear task_id único para tracking
        task_id = str(uuid.uuid4())[:8]
        
        # Registrar tarea
        task_add_task(
            task_id=task_id,
            task_name=opcion.label,
            target=target_host if target_host else "N/A",
            playbook=opcion.playbook
        )
        
        # Ejecutar según el modo
        if execution_mode == "new_window" and ejecutar_playbook_nueva_ventana:
            if target_host:
                result = ejecutar_playbook_nueva_ventana(
                    hostname=target_host,
                    playbook_path=opcion.playbook,
                    vault_password=vault_password,
                    extra_vars=extra_vars if extra_vars else None
                )
                results.append(result)
        elif execution_mode == "background":
            # Ejecutar en background (thread)
            def execute_and_track():
                try:
                    result = ejecutar_playbook(
                        hostname=target_host if target_host else "localhost",
                        playbook_path=opcion.playbook,
                        vault_password=vault_password,
                        extra_vars=extra_vars if extra_vars else None,
                        background=False  # No usar BackgroundEngine, lo manejamos nosotros
                    )
                    # Actualizar tarea
                    status = "SUCCESS" if result.success else "FAILED"
                    task_update_task(task_id, status, result, result.stderr if not result.success else None)
                    # Guardar en historial
                    if target_host:
                        history_add_entry(target_host, opcion.label, result)
                except Exception as e:
                    # En caso de error no manejado, marcar tarea como fallida
                    from .config import logger
                    logger.error(f"Error en thread {task_id}: {e}", exc_info=True)
                    task_update_task(task_id, "FAILED", error=str(e))
            
            import threading
            thread = threading.Thread(target=execute_and_track, daemon=True)
            thread.start()
            results.append(None)  # Placeholder para background
        else:
            # Ejecución normal
            result = ejecutar_playbook(
                hostname=target_host if target_host else "localhost",
                playbook_path=opcion.playbook,
                vault_password=vault_password,
                extra_vars=extra_vars if extra_vars else None,
                interactive=(opcion.key == "C1")
            )
            
            # Actualizar tarea
            status = "SUCCESS" if result.success else "FAILED"
            task_update_task(task_id, status, result, result.stderr if not result.success else None)
            results.append(result)
            
            # Guardar en el historial
            if target_host:
                history_add_entry(target_host, opcion.label, result)
            
            # Mostrar resultados según el tipo de opción (solo para primer target en modo normal)
            if target_host == targets[0] and not opcion.can_new_window:
                if opcion.key == "H1":  # Specs
                    mostrar_specs_tabla(result, target_host)
                elif opcion.key == "A2":  # LAPS
                    mostrar_laps_resultado(result, target_host)
                elif opcion.key == "A3":  # BitLocker Key
                    mostrar_bitlocker_resultado(result, target_host)
                elif opcion.key == "H9":  # Windows Updates
                    mostrar_updates_resultado(result, target_host)
                elif opcion.key == "A5":  # BitLocker Status
                    mostrar_bitlocker_status_tabla(result, target_host)
                elif opcion.key == "A4":  # AD Info
                    mostrar_ad_info(result, target_host)
                elif opcion.key == "A6":  # AD Groups
                    mostrar_audit_groups_resultado(result, target_host)
                elif opcion.key == "H10":  # Health Audit Combo
                    mostrar_auditoria_salud(result, target_host)
                else:
                    mostrar_resultado(result, opcion.label)
                
                # Opción de guardar reporte para tareas clave
                if opcion.key in ["H1", "H7", "H8", "H9", "H10", "A4", "A6"]:
                    if questionary.confirm("¿Deseas guardar este resultado como un reporte HTML?", default=False, style=CUSTOM_STYLE).ask():
                        guardar_reporte(target_host)
    
    # Mensaje final
    if execution_mode == "background":
        active_count = len(targets)
        console.print(f"\n[green]✅ {active_count} tarea(s) iniciada(s) en segundo plano[/green]")
        console.print(f"[dim]Monitoreando {active_count} equipo(s): {', '.join(targets)}[/dim]\n")
    elif execution_mode == "new_window":
        console.print(f"\n[green]✅ Consola remota abierta en nueva ventana[/green]\n")
    
    # Esperar antes de volver al menú (solo para modo normal con un solo target)
    if execution_mode == "normal" and len(targets) == 1 and not opcion.can_new_window:
        console.print("")
        questionary.press_any_key_to_continue(
            "Presione cualquier tecla para continuar..."
        ).ask()
