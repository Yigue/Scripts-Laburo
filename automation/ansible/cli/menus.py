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
    mostrar_dashboard_ejecucion, mostrar_historial_sesion,
    mostrar_metricas_resultado, mostrar_health_resultado
)
from .history import add_entry as history_add_entry

# Intentar importar ejecutar_playbook_nueva_ventana si existe
try:
    from .ansible_runner import ejecutar_playbook_nueva_ventana
except ImportError:
    ejecutar_playbook_nueva_ventana = None


def mostrar_menu_categorias() -> Optional[MenuCategory]:
    """
    Muestra el menú de categorías con navegación por letras/números.
    
    Returns:
        MenuCategory: La categoría seleccionada, o None si cancela/sale
    """
    # Preparar opciones con claves visibles para navegación rápida
    choices = []
    used_shortcuts = set()
    
    # Mapeo de categorías a atajos únicos
    category_shortcuts = {
        "A": "a",  # Admin
        "H": "h",  # Hardware
        "R": "r",  # Redes
        "S": "s",  # Software
        "I": "i",  # Impresoras
        "C": "c",  # Consola
        "SC": "1",  # SCCM (usar número para evitar conflicto)
        "WL": "2",  # WLC (usar número para evitar conflicto)
        "M": "m",  # Monitoring
    }
    
    for cat in MENU_CATEGORIES:
        shortcut = category_shortcuts.get(cat.key, None)
        if shortcut and shortcut not in used_shortcuts:
            choices.append(questionary.Choice(
                title=f"[{shortcut.upper()}] {cat.icon} {cat.name}",
                value=cat,
                shortcut_key=shortcut
            ))
            used_shortcuts.add(shortcut)
        else:
            # Si no hay shortcut disponible, no usar atajo
            choices.append(f"{cat.icon} {cat.name}")
    
    choices.append(questionary.Separator())
    # Historial usa "H" pero ya está usado por Hardware, usar "0" o letra alternativa
    choices.append(questionary.Choice(
        title="[0] 📜 Historial",
        value="HI",
        shortcut_key="0"
    ))
    choices.append(questionary.Choice(
        title="[D] 📊 Dashboard",
        value="D",
        shortcut_key="d"
    ))
    choices.append(questionary.Choice(
        title="[Q] ❌ Salir",
        value=None,
        shortcut_key="q"
    ))
    
    answer = questionary.select(
        "Seleccione una opción (usa letras/números para navegar rápido):",
        choices=choices,
        style=CUSTOM_STYLE,
        use_indicator=True,
        use_shortcuts=True
    ).ask()
    
    if answer is None or answer == "HI" or answer == "D":
        # Manejar respuestas especiales
        if answer == "HI":
            return MenuCategory(key="HI", name="Historial", icon="📜", options=[])
        elif answer == "D":
            return MenuCategory(key="D", name="Dashboard", icon="📊", options=[])
        return None
    
    # Si la respuesta es una categoría, retornarla directamente
    if isinstance(answer, MenuCategory):
        return answer
    
    # Fallback: buscar por nombre
    for cat in MENU_CATEGORIES:
        if hasattr(answer, 'name') and cat.name == answer.name:
            return cat
        elif isinstance(answer, str) and (cat.name in answer or cat.icon in answer):
            return cat
    
    return None


def mostrar_menu_opciones(categoria: MenuCategory) -> Optional[MenuOption]:
    """
    Muestra las opciones de una categoría con navegación por números.
    
    Args:
        categoria: La categoría cuyas opciones mostrar
        
    Returns:
        MenuOption: La opción seleccionada, o None si vuelve atrás
    """
    choices = []
    
    # Agregar opciones con números como atajos (1-9, luego letras si es necesario)
    # Para más de 9 opciones, usar la primera letra del número (ej: 10 -> a, 11 -> b)
    shortcut_keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
    
    for idx, opt in enumerate(categoria.options):
        # Mostrar clave de opción (A1, H1, etc.) como prefijo visible
        display_label = f"[{opt.key}] {opt.label}" if opt.key else opt.label
        
        # Asignar atajo numérico para las primeras 9 opciones
        if idx < 9:
            shortcut = shortcut_keys[idx]
            choices.append(questionary.Choice(
                title=display_label,
                value=opt,
                shortcut_key=shortcut
            ))
        else:
            # Para más de 9 opciones, usar el número completo como parte del título
            choices.append(questionary.Choice(
                title=f"[{idx+1}] {opt.label}",
                value=opt
            ))
    
    choices.append(questionary.Separator())
    choices.append(questionary.Choice(
        title="[V] ← Volver",
        value=None,
        shortcut_key="v"
    ))
    
    answer = questionary.select(
        f"{categoria.icon} {categoria.name}",
        choices=choices,
        style=CUSTOM_STYLE,
        use_indicator=True,
        use_shortcuts=True
    ).ask()
    
    if answer is None:
        return None
    
    # Si la respuesta es una opción, retornarla directamente
    if isinstance(answer, MenuOption):
        return answer
    
    # Fallback: buscar por label
    if isinstance(answer, str):
        for opt in categoria.options:
            if opt.label in answer or opt.key in answer:
                return opt
    
    return None


def _validar_script_powershell(script: str) -> Optional[str]:
    """
    Valida un script PowerShell antes de ejecutarlo remotamente.
    
    Args:
        script: El script a validar
        
    Returns:
        El script validado, o None si el usuario cancela después de advertencia
    """
    import re
    
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
        r'\bInvoke-Expression\s*\(\s*[^\)]*Get-Content\s+[^\)]*\)',  # Invoke-Expression con Get-Content (técnica de bypass)
        r'\bStart-Process\s+-FilePath\s+["\']?C:\\Windows\\System32\\shutdown',
        r'\bStop-Computer\s+-Force',
        r'\bRestart-Computer\s+-Force',
        r'\bClear-EventLog',
        r'\bRemove-EventLog',
    ]
    
    # Detectar comandos peligrosos
    script_lower = script.lower()
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
    #region agent log
    import json
    log_path = "/home/korg/Scripts-Laburo/automation/ansible/.cursor/debug.log"
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "cli/menus.py:116", "message": "ejecutar_opcion INICIO", "data": {"opcion_key": opcion.key, "opcion_label": opcion.label, "requires_hostname": opcion.requires_hostname, "has_vault": vault_password is not None}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except: pass
    #endregion
    console.print(f"\n[cyan]▶ Ejecutando: {opcion.label}[/cyan]")
    console.print(f"[dim]{opcion.description}[/dim]\n")
    
    # Si la opción requiere hostname, solicitarlo (o múltiples targets)
    targets = []
    if opcion.requires_hostname:
        #region agent log
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "cli/menus.py:138", "message": "Requiere hostname", "data": {"hostname_provided": hostname}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except: pass
        #endregion
        if hostname is None:
            # Solicitar targets (1 o múltiples)
            targets_input = solicitar_targets()
            #region agent log
            try:
                with open(log_path, "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "cli/menus.py:142", "message": "Después de solicitar_targets", "data": {"targets_input": targets_input, "is_none": targets_input is None}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
            #endregion
            if targets_input is None:
                console.print("[yellow]Operación cancelada[/yellow]")
                #region agent log
                try:
                    with open(log_path, "a") as f:
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "cli/menus.py:144", "message": "Operación cancelada - targets None", "data": {}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
                except: pass
                #endregion
                return
            targets = targets_input
        else:
            targets = [hostname]
    else:
        # No requiere hostname (p. ej. AD unlock solo necesita username)
        # El playbook usará domain_controller automáticamente si target_host está vacío
        targets = [""]  # Target vacío para opciones que no requieren hostname
    #region agent log
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "cli/menus.py:151", "message": "Targets determinados", "data": {"targets": targets, "count": len(targets)}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except: pass
    #endregion
    
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
        
        # Validación de seguridad para scripts PowerShell (opción C2)
        if opcion.key == "C2" and opcion.input_var_name == "custom_script":
            user_input = _validar_script_powershell(user_input)
            if user_input is None:
                return  # El usuario canceló después de la advertencia
        
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
                #region agent log
                log_path_bg = "/home/korg/Scripts-Laburo/automation/ansible/.cursor/debug.log"
                import json
                try:
                    with open(log_path_bg, "a") as f:
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "cli/menus.py:232", "message": "Thread background INICIO", "data": {"target_host": target_host, "playbook": opcion.playbook}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
                except: pass
                #endregion
                try:
                    # Para opciones que no requieren hostname (requires_hostname=False),
                    # pasar "localhost" como placeholder. El playbook usará domain_controller
                    # automáticamente cuando detecte que target_host es "localhost"
                    hostname_to_use = target_host if target_host else "localhost"
                    if not opcion.requires_hostname and not target_host:
                        # Opciones AD que no requieren hostname usan domain_controller
                        hostname_to_use = "localhost"  # El playbook manejará esto correctamente
                    
                    result = ejecutar_playbook(
                        hostname=hostname_to_use,
                        playbook_path=opcion.playbook,
                        vault_password=vault_password,
                        extra_vars=extra_vars if extra_vars else None
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
            #region agent log
            try:
                with open(log_path, "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "cli/menus.py:258", "message": "Antes de ejecutar_playbook (normal)", "data": {"target_host": target_host, "playbook": opcion.playbook, "has_vault": vault_password is not None, "has_extra_vars": bool(extra_vars), "interactive": opcion.key == "C1"}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
            #endregion
            try:
                # Para opciones que no requieren hostname (requires_hostname=False),
                # pasar "localhost" como placeholder. El playbook usará domain_controller
                # automáticamente cuando detecte que target_host es "localhost"
                hostname_to_use = target_host if target_host else "localhost"
                if not opcion.requires_hostname and not target_host:
                    # Opciones AD que no requieren hostname usan domain_controller
                    hostname_to_use = "localhost"  # El playbook manejará esto correctamente
                
                result = ejecutar_playbook(
                    hostname=hostname_to_use,
                    playbook_path=opcion.playbook,
                    vault_password=vault_password,
                    extra_vars=extra_vars if extra_vars else None,
                    interactive=(opcion.key == "C1")
                )
                #region agent log
                try:
                    with open(log_path, "a") as f:
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "cli/menus.py:266", "message": "Después de ejecutar_playbook", "data": {"success": result.success, "returncode": result.returncode, "has_stderr": bool(result.stderr)}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
                except: pass
                #endregion
            except Exception as e:
                #region agent log
                try:
                    with open(log_path, "a") as f:
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "cli/menus.py:269", "message": "Error en ejecutar_playbook", "data": {"error_type": type(e).__name__, "error_msg": str(e)}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
                except: pass
                #endregion
                raise
            
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
                elif opcion.key == "M1":  # Métricas
                    mostrar_metricas_resultado(result, target_host)
                elif opcion.key == "M2":  # Health Checks
                    mostrar_health_resultado(result, target_host)
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
