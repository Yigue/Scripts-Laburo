# -*- coding: utf-8 -*-
"""
cli/__init__.py
===============
IT-Ops CLI - Paquete principal.

Este paquete contiene los módulos de la CLI de IT-Ops:
- config: Configuración global (paths, logging, console)
- models: Dataclasses para datos estructurados
- menu_data: Definición del menú completo
- ansible_runner: Funciones de ejecución de Ansible
- display: Funciones de visualización con Rich
- prompts: Funciones de entrada de usuario
- menus: Funciones de navegación de menú
"""

from .config import BASE_DIR, console, logger, CUSTOM_STYLE
from .models import MenuOption, MenuCategory, ExecutionResult, HostSnapshot
from .menu_data import MENU_CATEGORIES
from .ansible_runner import (
    check_environment, validate_hostname, check_online, 
    ejecutar_playbook, obtener_host_snapshot, repair_winrm_local
)
from .display import (
    clear_screen, show_banner, show_menu_summary,
    mostrar_resultado, mostrar_specs_tabla, 
    mostrar_laps_resultado, mostrar_bitlocker_resultado,
    mostrar_host_snapshot, mostrar_updates_resultado,
    mostrar_bitlocker_status_tabla, mostrar_ad_info,
    mostrar_dashboard_ejecucion, mostrar_audit_groups_resultado,
    mostrar_auditoria_salud, guardar_reporte
)
from .prompts import solicitar_hostname, solicitar_vault_password, interactive_confirm
from .menus import mostrar_menu_categorias, mostrar_menu_opciones, ejecutar_opcion
