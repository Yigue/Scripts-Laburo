# -*- coding: utf-8 -*-
"""
cli/__init__.py
===============
IT-Ops CLI - Paquete principal (refactorizado con Clean Architecture).

Wrappers de compatibilidad para mantener retrocompatibilidad con imports antiguos.
"""

# ============================================================================
# Shared (Configuración)
# ============================================================================
from .shared.config import BASE_DIR, console, logger, CUSTOM_STYLE

# ============================================================================
# Domain (Modelos)
# ============================================================================
from .domain.models import MenuOption, MenuCategory, ExecutionResult, HostSnapshot, ExecutionStats
from .menu_data import MENU_CATEGORIES

# ============================================================================
# Domain Services
# ============================================================================
from .domain.services.validation_service import check_environment, validate_hostname

# ============================================================================
# Infrastructure (Ansible)
# ============================================================================
from .infrastructure.ansible.playbook_executor import execute_playbook as _execute_playbook
from .infrastructure.ansible.health_checker import check_host_online as _check_host_online, get_host_snapshot as _get_host_snapshot
from .infrastructure.ansible.winrm_repair import repair_winrm_local

# Wrappers de compatibilidad (usar nombres antiguos)
def ejecutar_playbook(*args, **kwargs):
    """Wrapper de compatibilidad para execute_playbook."""
    return _execute_playbook(*args, **kwargs)

def check_online(*args, **kwargs):
    """Wrapper de compatibilidad para check_host_online."""
    return _check_host_online(*args, **kwargs)

def obtener_host_snapshot(*args, **kwargs):
    """Wrapper de compatibilidad para get_host_snapshot."""
    return _get_host_snapshot(*args, **kwargs)

# Intentar importar ejecutar_playbook_nueva_ventana
try:
    from .infrastructure.terminal.terminal_detector import execute_playbook_in_new_window as ejecutar_playbook_nueva_ventana
except ImportError:
    ejecutar_playbook_nueva_ventana = None

# ============================================================================
# Presentation (Display)
# ============================================================================
from .presentation.display.utils import clear_screen, show_banner, show_menu_summary
from .presentation.display.general_formatters import (
    mostrar_resultado, mostrar_host_snapshot, mostrar_historial_sesion,
    mostrar_dashboard_ejecucion, guardar_reporte
)
from .presentation.display.hardware_formatters import (
    mostrar_specs_tabla, mostrar_updates_resultado,
    mostrar_bitlocker_status_tabla, mostrar_auditoria_salud
)
from .presentation.display.admin_formatters import (
    mostrar_laps_resultado, mostrar_bitlocker_resultado,
    mostrar_ad_info, mostrar_audit_groups_resultado
)
from .presentation.display.monitoring_formatters import (
    mostrar_metricas_resultado, mostrar_health_resultado
)

# ============================================================================
# Presentation (CLI - Menus)
# ============================================================================
from .presentation.cli.menus import mostrar_menu_categorias, mostrar_menu_opciones
from .presentation.cli.menu_handler import ejecutar_opcion

# ============================================================================
# Presentation (Prompts)
# ============================================================================
from .prompts import solicitar_hostname, solicitar_vault_password, interactive_confirm, solicitar_targets

# ============================================================================
# Legacy modules (mantener por compatibilidad)
# ============================================================================
from .history import add_entry as history_add_entry, get_entries as history_get_entries
from .task_manager import (
    add_task as task_add_task,
    update_task as task_update_task,
    get_active_tasks as task_get_active_tasks,
    get_all_tasks as task_get_all_tasks,
    get_task as task_get_task,
    get_summary as task_get_summary,
    TaskStatus
)
from .task_panel import get_task_panel, render_task_panel
