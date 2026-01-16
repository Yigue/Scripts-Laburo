# -*- coding: utf-8 -*-
"""
cli/menu_data.py
================
Definición del menú completo de la aplicación.

Este archivo contiene MENU_CATEGORIES, la lista de todas las
categorías y opciones disponibles en el menú interactivo.
"""

from .models import MenuOption, MenuCategory


# ============================================================================
# DEFINICIÓN DEL MENÚ COMPLETO
# ============================================================================
MENU_CATEGORIES = [
    # =========================================================================
    # [A] ADMIN & DOMINIO
    # =========================================================================
    MenuCategory(
        key="A",
        name="Admin & Dominio",
        icon="🔐",
        options=[
            MenuOption(
                "A1", "Desbloquear usuario de red (AD)", "admin/unlock_user.yml",
                "Desbloquea una cuenta de usuario bloqueada en Active Directory",
                requires_input=True, input_prompt="Username a desbloquear", input_var_name="ad_username"
            ),
            MenuOption(
                "A2", "Obtener password Admin Local (LAPS)", "admin/get_laps_password.yml",
                "Obtiene la contraseña LAPS del administrador local desde AD"
            ),
            MenuOption(
                "A3", "Ver clave BitLocker Recovery (AD)", "admin/get_bitlocker_key.yml",
                "Obtiene la clave de recuperación BitLocker (48 dígitos) desde AD"
            ),
            MenuOption(
                "A4", "Info de Equipo en AD", "admin/ad_info.yml",
                "Consulta datos del equipo en Active Directory (OS, creación, login)"
            ),
            MenuOption(
                "A5", "Estado de BitLocker", "admin/bitlocker_status.yml",
                "Verifica el estado de cifrado y protectores en C:"
            ),
            MenuOption(
                "A6", "Auditoría de Grupos de AD", "admin/audit_groups.yml",
                "Muestra los grupos de seguridad en los que está el equipo"
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
        options=[
            MenuOption(
                "H1", "Mostrar especificaciones", "hardware/specs.yml",
                "Obtiene info del sistema: CPU, RAM, disco, red"
            ),
            MenuOption(
                "H2", "Terminar de configurar", "hardware/configure.yml",
                "Ejecuta tareas de configuración inicial"
            ),
            MenuOption(
                "H3", "Optimizar sistema", "hardware/optimize.yml",
                "Limpieza de disco, desfragmentación, etc."
            ),
            MenuOption(
                "H4", "Reiniciar equipo", "hardware/reboot.yml",
                "Reinicia el equipo de forma controlada"
            ),
            MenuOption(
                "H5", "Actualizar drivers DELL", "hardware/dell_drivers.yml",
                "Ejecuta Dell Command Update"
            ),
            MenuOption(
                "H6", "Activar Windows", "hardware/activate_windows.yml",
                "Activa Windows con KMS"
            ),
            MenuOption(
                "H7", "Salud de Batería (Laptop)", "hardware/battery_health.yml",
                "Genera reporte de salud de batería (solo laptops)"
            ),
            MenuOption(
                "H8", "Reporte SMART de Disco", "hardware/disk_smart.yml",
                "Diagnóstico S.M.A.R.T. de discos duros y SSD"
            ),
            MenuOption(
                "H9", "Buscar Windows Updates", "hardware/check_updates.yml",
                "Busca actualizaciones de Windows pendientes sin instalar"
            ),
            MenuOption(
                "H10", "Auditoría General de Salud (Combo)", "hardware/health_audit.yml",
                "Ejecuta un diagnóstico completo: Specs, Batería, SMART y Updates"
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
        options=[
            MenuOption(
                "R1", "WCORP Fix", "network/wcorp_fix.yml",
                "Script WCORP + cleanDNS + gpupdate"
            ),
            MenuOption(
                "R2", "Analizador Wi-Fi", "network/wifi_analyzer.yml",
                "Información detallada de conexión Wi-Fi, AP y señal"
            ),
            MenuOption(
                "R3", "Reparar red", "network/network_repair.yml",
                "Flush DNS, reset IP, reiniciar adaptador"
            ),
            MenuOption(
                "R4", "Test de Velocidad", "network/speedtest.yml",
                "Test de velocidad de Internet (descarga, latencia, jitter)"
            ),
            MenuOption(
                "R5", "Ver consumo de ancho de banda", "network/bandwidth_usage.yml",
                "Estadísticas de uso de red en tiempo real"
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
        options=[
            MenuOption(
                "S1", "Instalar Office 365", "software/install_office.yml",
                "Instalación silenciosa de Office 365"
            ),
            MenuOption(
                "S2", "Reparar Office", "software/repair_office.yml",
                "Ejecuta Quick Repair de Office"
            ),
            MenuOption(
                "S3", "Resetear OneDrive", "software/reset_onedrive.yml",
                "Resetea OneDrive a su configuración inicial"
            ),
            MenuOption(
                "S4", "Gestionar aplicaciones", "software/manage_apps.yml",
                "Listar, buscar y desinstalar aplicaciones"
            ),
            MenuOption(
                "S5", "Listar aplicaciones instaladas", "software/list_apps.yml",
                "Exporta una lista completa del software instalado"
            ),
            MenuOption(
                "S6", "Limpieza profunda de temporales", "software/deep_clean.yml",
                "Borra caché de Teams, Outlook y carpetas Temp del sistema"
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
        options=[
            MenuOption(
                "I1", "Gestionar impresoras", "printers/manage_printers.yml",
                "Gestión de spooler e impresoras"
            ),
            MenuOption(
                "I2", "Calibrar Zebra", "printers/zebra_calibrate.yml",
                "Envía comando de calibración a impresora Zebra",
                requires_input=True, input_prompt="IP de la impresora Zebra", input_var_name="zebra_ip"
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
        options=[
            MenuOption(
                "C1", "Abrir consola remota", "remote/console.yml",
                "Consola PowerShell interactiva"
            ),
            MenuOption(
                "C2", "Ejecutar comando/script custom", "remote/custom_command.yml", # Necesitaremos este playbook
                "Pega un comando PowerShell y ejecútalo remotamente",
                requires_input=True, input_prompt="Script PowerShell a ejecutar", input_var_name="custom_script"
            ),
        ]
    ),
]
