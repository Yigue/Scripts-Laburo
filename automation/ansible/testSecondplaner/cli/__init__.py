# -*- coding: utf-8 -*-
"""
cli/__init__.py
===============
IT-Ops CLI - Paquete principal mejorado.
"""

from .config import BASE_DIR, console, logger, CUSTOM_STYLE
from .models import MenuOption, MenuCategory, ExecutionResult, HostSnapshot
from .menu_data import MENU_CATEGORIES
from .ansible_runner import (
    check_environment, validate_hostname, check_online, 
    ejecutar_playbook, ejecutar_playbook_nueva_ventana,
    obtener_host_snapshot
)
from .display import (
    clear_screen, show_banner, show_menu_summary,
    mostrar_resultado, mostrar_specs_tabla, 
    mostrar_laps_resultado, mostrar_bitlocker_resultado,
    mostrar_host_snapshot, mostrar_updates_resultado,
    mostrar_bitlocker_status_tabla, mostrar_ad_info,
    mostrar_dashboard_ejecucion, mostrar_audit_groups_resultado,
    mostrar_auditoria_salud, guardar_reporte, mostrar_historial_sesion
)
from .prompts import solicitar_hostname, solicitar_vault_password, interactive_confirm, solicitar_targets
from .menus import mostrar_menu_categorias, mostrar_menu_opciones, ejecutar_opcion
from .history import session_history
from .task_manager import task_manager
from .task_panel import get_task_panel, render_task_panel