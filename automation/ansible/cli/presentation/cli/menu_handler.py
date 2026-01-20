# -*- coding: utf-8 -*-
"""
presentation/cli/menu_handler.py
=================================
Handler para ejecutar opciones del menú.

Maneja la presentación, confirmación y presentación de resultados de opciones del menú.
"""

from typing import Optional, List, Dict
import questionary

from ...domain.models import MenuOption, ExecutionResult
from ...shared.config import console, CUSTOM_STYLE
from ...application.use_cases.ejecutar_opcion import (
    ejecutar_opcion_use_case,
    preparar_extra_vars,
    determinar_modo_ejecucion
)
from cli.prompts import solicitar_targets
from ..display.general_formatters import mostrar_resultado, guardar_reporte
from ..display.hardware_formatters import (
    mostrar_specs_tabla,
    mostrar_updates_resultado,
    mostrar_bitlocker_status_tabla,
    mostrar_auditoria_salud
)
from ..display.monitoring_formatters import (
    mostrar_metricas_resultado,
    mostrar_health_resultado
)
from ..display.admin_formatters import (
    mostrar_laps_resultado,
    mostrar_bitlocker_resultado,
    mostrar_ad_info,
    mostrar_audit_groups_resultado
)
from ...infrastructure.logging.debug_logger import debug_logger


def ejecutar_opcion(
    opcion: MenuOption,
    hostname: Optional[str] = None,
    vault_password: Optional[str] = None
):
    """
    Ejecuta una opción del menú mejorada con soporte para segundo plano y nueva ventana.
    
    Args:
        opcion: La opción de menú a ejecutar
        hostname: Hostname del equipo destino (opcional)
        vault_password: Password del vault (opcional)
    """
    debug_logger.log(
        "presentation/cli/menu_handler.py:40",
        "ejecutar_opcion INICIO",
        {
            "opcion_key": opcion.key,
            "opcion_label": opcion.label,
            "requires_hostname": opcion.requires_hostname,
            "has_vault": vault_password is not None
        },
        hypothesis_id="B"
    )
    
    console.print(f"\n[cyan]▶ Ejecutando: {opcion.label}[/cyan]")
    console.print(f"[dim]{opcion.description}[/dim]\n")
    
    # Determinar targets
    targets = _determinar_targets(opcion, hostname)
    if targets is None:
        console.print("[yellow]Operación cancelada[/yellow]")
        return
    
    # Preparar variables extra
    try:
        extra_vars = _solicitar_extra_vars(opcion)
        if extra_vars is None:
            console.print("[yellow]Operación cancelada[/yellow]")
            return
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        return
    
    # Confirmar ejecución si es necesario
    if not _confirmar_ejecucion(opcion, targets):
        console.print("[yellow]Operación cancelada[/yellow]")
        return
    
    # Verificar si puede ejecutarse en nueva ventana
    can_new_window = False
    try:
        from ...infrastructure.terminal.terminal_detector import execute_playbook_in_new_window
        can_new_window = (execute_playbook_in_new_window is not None)
    except ImportError:
        pass
    
    # Determinar modo de ejecución
    execution_mode = determinar_modo_ejecucion(opcion, targets, can_new_window)
    
    if execution_mode == "new_window":
        console.print("[cyan]ℹ Se abrirá en una nueva ventana para interacción directa[/cyan]\n")
    
    # Ejecutar
    results = ejecutar_opcion_use_case(
        opcion=opcion,
        targets=targets,
        vault_password=vault_password,
        extra_vars=extra_vars,
        execution_mode=execution_mode
    )
    
    # Mostrar resultados
    _mostrar_resultados(opcion, targets, results, execution_mode)
    
    # Esperar antes de volver al menú (solo para modo normal con un solo target)
    if execution_mode == "normal" and len(targets) == 1 and not opcion.can_new_window:
        console.print("")
        questionary.press_any_key_to_continue(
            "Presione cualquier tecla para continuar..."
        ).ask()


def _determinar_targets(opcion: MenuOption, hostname: Optional[str]) -> Optional[List[str]]:
    """Determina los targets para ejecutar."""
    if opcion.requires_hostname:
        if hostname is None:
            targets_input = solicitar_targets()
            if targets_input is None:
                return None
            return targets_input
        return [hostname]
    else:
        return [""]  # Target vacío para opciones que no requieren hostname


def _solicitar_extra_vars(opcion: MenuOption) -> Optional[Dict[str, str]]:
    """Solicita variables extra si la opción las requiere."""
    if not opcion.requires_input:
        return {}
    
    user_input = questionary.text(
        opcion.input_prompt + ":",
        style=CUSTOM_STYLE
    ).ask()
    
    if user_input is None:
        return None
    
    return preparar_extra_vars(opcion, user_input)


def _confirmar_ejecucion(opcion: MenuOption, targets: List[str]) -> bool:
    """Confirma la ejecución si no es read-only."""
    if opcion.action_type == "read-only":
        return True
    
    target_str = f" en {', '.join(targets)}" if targets and targets[0] else ""
    confirm = questionary.confirm(
        f"¿Ejecutar '{opcion.label}'{target_str}?",
        style=CUSTOM_STYLE,
        default=True
    ).ask()
    
    return confirm if confirm else False


def _mostrar_resultados(
    opcion: MenuOption,
    targets: List[str],
    results: List[Optional[ExecutionResult]],
    execution_mode: str
):
    """Muestra los resultados según el tipo de opción."""
    if execution_mode == "background":
        active_count = len(targets)
        console.print(f"\n[green]✅ {active_count} tarea(s) iniciada(s) en segundo plano[/green]")
        console.print(f"[dim]Monitoreando {active_count} equipo(s): {', '.join(targets)}[/dim]\n")
        return
    
    if execution_mode == "new_window":
        console.print(f"\n[green]✅ Consola remota abierta en nueva ventana[/green]\n")
        return
    
    # Mostrar resultados solo para primer target en modo normal
    if results and results[0] and targets:
        result = results[0]
        target_host = targets[0]
        
        # Mapear opciones a formateadores específicos
        _aplicar_formateador(opcion, result, target_host)
        
        # Opción de guardar reporte para tareas clave
        if opcion.key in ["H1", "H7", "H8", "H9", "H10", "A4", "A6"]:
            if questionary.confirm(
                "¿Deseas guardar este resultado como un reporte HTML?",
                default=False,
                style=CUSTOM_STYLE
            ).ask():
                guardar_reporte(target_host)


def _aplicar_formateador(opcion: MenuOption, result: ExecutionResult, hostname: str):
    """Aplica el formateador específico según la opción."""
    formatters = {
        "H1": mostrar_specs_tabla,
        "A2": mostrar_laps_resultado,
        "A3": mostrar_bitlocker_resultado,
        "H9": mostrar_updates_resultado,
        "A5": mostrar_bitlocker_status_tabla,
        "A4": mostrar_ad_info,
        "A6": mostrar_audit_groups_resultado,
        "H10": mostrar_auditoria_salud,
        "M1": mostrar_metricas_resultado,
        "M2": mostrar_health_resultado,
    }
    
    formatter = formatters.get(opcion.key)
    if formatter:
        formatter(result, hostname)
    else:
        mostrar_resultado(result, opcion.label)
