# -*- coding: utf-8 -*-
"""
cli/menu_data.py
================
Definición del menú completo mejorado con metadata.
"""

from .models import MenuOption, MenuCategory


# ============================================================================
# DEFINICIÓN DEL MENÚ COMPLETO MEJORADO
# ============================================================================
MENU_CATEGORIES = [
    # =========================================================================
    # [A] ADMIN & DOMINIO
    # =========================================================================
    MenuCategory(
        key="A",
        name="Admin & Dominio",
        icon="🔐",
        color="red",
        options=[
            MenuOption(
                "A1", "Desbloquear usuario de red (AD)", "playbooks/admin/unlock_user.yml",
                "Desbloquea una cuenta de usuario bloqueada en Active Directory",
                requires_input=True, input_prompt="Username a desbloquear", input_var_name="ad_username",
                action_type="modify", can_background=False, requires_hostname=False
            ),
            MenuOption(
                "A2", "Obtener password Admin Local (LAPS)", "playbooks/admin/get_laps_password.yml",
                "Obtiene la contraseña LAPS del administrador local desde AD",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "A3", "Ver clave BitLocker Recovery (AD)", "playbooks/admin/get_bitlocker_key.yml",
                "Obtiene la clave de recuperación BitLocker (48 dígitos) desde AD",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "A4", "Info de Equipo en AD", "playbooks/admin/ad_info.yml",
                "Consulta datos del equipo en Active Directory (OS, creación, login)",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "A5", "Estado de BitLocker", "playbooks/admin/bitlocker_status.yml",
                "Verifica el estado de cifrado y protectores en C:",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "A6", "Auditoría de Grupos de AD", "playbooks/admin/audit_groups.yml",
                "Muestra los grupos de seguridad en los que está el equipo",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
        ]
    ),
    # =========================================================================
    # [H] HARDWARE Y SISTEMA
    # =========================================================================
    MenuCategory(
        key="H",
        name="Hardware y Sistema",
        icon="💻",
        color="cyan",
        options=[
            MenuOption(
                "H1", "Mostrar especificaciones", "playbooks/hardware/specs.yml",
                "Obtiene info del sistema: CPU, RAM, disco, red",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "H2", "Terminar de configurar", "playbooks/hardware/configure.yml",
                "Ejecuta tareas de configuración inicial",
                action_type="modify", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "H3", "Optimizar sistema", "playbooks/hardware/optimize.yml",
                "Limpieza de disco, desfragmentación, etc.",
                action_type="modify", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "H4", "Reiniciar equipo", "playbooks/hardware/reboot.yml",
                "Reinicia el equipo de forma controlada",
                action_type="destructive", can_background=False, requires_hostname=True
            ),
            MenuOption(
                "H5", "Actualizar drivers DELL", "playbooks/hardware/dell_drivers.yml",
                "Ejecuta Dell Command Update",
                action_type="modify", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "H6", "Activar Windows", "playbooks/hardware/activate_windows.yml",
                "Activa Windows con KMS",
                action_type="modify", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "H7", "Salud de Batería (Laptop)", "playbooks/hardware/battery_health.yml",
                "Genera reporte de salud de batería (solo laptops)",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "H8", "Reporte SMART de Disco", "playbooks/hardware/disk_smart.yml",
                "Diagnóstico S.M.A.R.T. de discos duros y SSD",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "H9", "Buscar Windows Updates", "playbooks/hardware/check_updates.yml",
                "Busca actualizaciones de Windows pendientes sin instalar",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "H10", "Auditoría General de Salud (Combo)", "playbooks/hardware/health_audit.yml",
                "Ejecuta un diagnóstico completo: Specs, Batería, SMART y Updates",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
        ]
    ),
    # =========================================================================
    # [R] REDES Y CONECTIVIDAD
    # =========================================================================
    MenuCategory(
        key="R",
        name="Redes y Conectividad",
        icon="🌐",
        color="blue",
        options=[
            MenuOption(
                "R1", "WCORP Fix", "playbooks/network/wcorp_fix.yml",
                "Script WCORP + cleanDNS + gpupdate",
                action_type="modify", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "R2", "Analizador Wi-Fi", "playbooks/network/wifi_analyzer.yml",
                "Información detallada de conexión Wi-Fi, AP y señal",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "R3", "Reparar red", "playbooks/network/network_repair.yml",
                "Flush DNS, reset IP, reiniciar adaptador",
                action_type="modify", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "R4", "Test de Velocidad", "playbooks/network/speedtest.yml",
                "Test de velocidad de Internet (descarga, latencia, jitter)",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "R5", "Ver consumo de ancho de banda", "playbooks/network/bandwidth_usage.yml",
                "Estadísticas de uso de red en tiempo real",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
        ]
    ),
    # =========================================================================
    # [S] SOFTWARE
    # =========================================================================
    MenuCategory(
        key="S",
        name="Software",
        icon="📦",
        color="green",
        options=[
            MenuOption(
                "S1", "Instalar Office 365", "playbooks/software/install_office.yml",
                "Instalación silenciosa de Office 365",
                action_type="modify", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "S2", "Reparar Office", "playbooks/software/repair_office.yml",
                "Ejecuta Quick Repair de Office",
                action_type="modify", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "S3", "Resetear OneDrive", "playbooks/software/reset_onedrive.yml",
                "Resetea OneDrive a su configuración inicial",
                action_type="modify", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "S4", "Gestionar aplicaciones", "playbooks/software/manage_apps.yml",
                "Listar, buscar y desinstalar aplicaciones",
                action_type="modify", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "S5", "Listar aplicaciones instaladas", "playbooks/software/list_apps.yml",
                "Exporta una lista completa del software instalado",
                action_type="read-only", can_background=True, requires_hostname=True
            ),
        ]
    ),
    # =========================================================================
    # [I] IMPRESORAS
    # =========================================================================
    MenuCategory(
        key="I",
        name="Impresoras",
        icon="🖨️",
        color="magenta",
        options=[
            MenuOption(
                "I1", "Gestionar impresoras", "playbooks/printers/manage_printers.yml",
                "Gestión de spooler e impresoras",
                action_type="modify", can_background=True, requires_hostname=True
            ),
            MenuOption(
                "I2", "Calibrar Zebra", "playbooks/printers/zebra_calibrate.yml",
                "Envía comando de calibración a impresora Zebra",
                requires_input=True, input_prompt="IP de la impresora Zebra", input_var_name="zebra_ip",
                action_type="modify", can_background=False, requires_hostname=True
            ),
        ]
    ),
    # =========================================================================
    # [C] CONSOLA REMOTA
    # =========================================================================
    MenuCategory(
        key="C",
        name="Consola Remota",
        icon="🖥️",
        color="yellow",
        options=[
            MenuOption(
                "C1", "Abrir consola remota", "playbooks/remote/console.yml",
                "Consola PowerShell interactiva",
                action_type="read-only", can_background=False, can_new_window=True, requires_hostname=True
            ),
        ]
    ),
]
