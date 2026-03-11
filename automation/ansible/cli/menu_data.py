# -*- coding: utf-8 -*-
"""
cli/menu_data.py
================
Definición del menú completo de la aplicación.

Este archivo contiene MENU_CATEGORIES, la lista de todas las
categorías y opciones disponibles en el menú interactivo.
"""

from .domain.models import MenuOption, MenuCategory


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
                requires_input=True, input_prompt="Username a desbloquear", input_var_name="ad_username",
                action_type="modify", requires_hostname=False
            ),
            MenuOption(
                "A2", "Obtener password Admin Local (LAPS)", "admin/get_laps_password.yml",
                "Obtiene la contraseña LAPS del administrador local desde AD",
                action_type="read-only"
            ),
            # MenuOption(
            #     "A3", "Ver clave BitLocker Recovery (AD)", "admin/get_bitlocker_key.yml",
            #     "Obtiene la clave de recuperación BitLocker (48 dígitos) desde AD",
            #     action_type="read-only"
            # ),
            MenuOption(
                "A4", "Info de Equipo en AD", "admin/ad_info.yml",
                "Consulta datos del equipo en Active Directory (OS, creación, login)",
                action_type="read-only", requires_hostname=True
            ),
            # MenuOption(
            #     "A5", "Estado de BitLocker", "admin/bitlocker_status.yml",
            #     "Verifica el estado de cifrado y protectores en C:",
            #     action_type="read-only"
            # ),
            # MenuOption(
            #     "A6", "Auditoría de Grupos de AD", "admin/audit_groups.yml",
            #     "Muestra los grupos de seguridad en los que está el equipo",
            #     action_type="read-only"
            # ),
            # MenuOption(
            #     "A7", "Auditoría de usuarios inactivos", "admin/audit_inactive.yml",
            #     "Lista usuarios de AD que no han iniciado sesión recientemente",
            #     action_type="read-only"
            # ),
            # MenuOption(
            #     "A8", "Exportar reporte de AD", "admin/export_ad_report.yml",
            #     "Genera un reporte completo de equipos en Active Directory",
            #     action_type="read-only"
            # ),
            # MenuOption(
            #     "A9", "Obtener miembros de grupo AD", "admin/get_group_members.yml",
            #     "Lista todos los miembros de un grupo de seguridad de AD",
            #     requires_input=True, input_prompt="Nombre del grupo AD", input_var_name="group_name",
            #     action_type="read-only", requires_hostname=False
            # ),
            # MenuOption(
            #     "A10", "Listar computadoras en AD", "admin/list_ad_computers.yml",
            #     "Lista todas las computadoras registradas en Active Directory",
            #     action_type="read-only", requires_hostname=False
            # ),
            # MenuOption(
            #     "A11", "Listar usuarios en AD", "admin/list_ad_users.yml",
            #     "Lista todos los usuarios registrados en Active Directory",
            #     action_type="read-only", requires_hostname=False
            # ),
            # MenuOption(
            #     "A12", "Validar atributos de AD", "admin/validate_attributes.yml",
            #     "Verifica que los atributos requeridos estén presentes en objetos AD",
            #     action_type="read-only"
            # ),
            MenuOption(
                "A13", "🔧 Mantenimiento Completo", "admin/full_maintenance.yml",
                "Ejecuta TODAS las acciones de mantenimiento: gpupdate, flush DNS, limpieza, ciclos SCCM, servicios, sincronización de hora",
                action_type="modify"
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
                "Obtiene info del sistema: CPU, RAM, disco, red",
                action_type="read-only"
            ),
            MenuOption(
                "H2", "Terminar de configurar", "hardware/configure.yml",
                "Ejecuta tareas de configuración inicial",
                action_type="modify"
            ),
            MenuOption(
                "H3", "Optimizar sistema", "hardware/optimize.yml",
                "Limpieza de disco, desfragmentación, etc.",
                action_type="modify"
            ),
            MenuOption(
                "H4", "Reiniciar equipo", "hardware/reboot.yml",
                "Reinicia el equipo de forma controlada",
                action_type="destructive", can_background=False
            ),
            MenuOption(
                "H5", "Actualizar drivers DELL", "hardware/dell_drivers.yml",
                "Ejecuta Dell Command Update",
                action_type="modify"
            ),
            MenuOption(
                "H6", "Activar Windows", "hardware/activate_windows.yml",
                "Activa Windows con KMS",
                action_type="modify"
            ),
            # MenuOption(
            #     "H7", "Salud de Batería (Laptop)", "hardware/battery_health.yml",
            #     "Genera reporte de salud de batería (solo laptops)",
            #     action_type="read-only"
            # ),
            # MenuOption(
            #     "H8", "Reporte SMART de Disco", "hardware/disk_smart.yml",
            #     "Diagnóstico S.M.A.R.T. de discos duros y SSD",
            #     action_type="read-only"
            # ),
            MenuOption(
                "H9", "Buscar Windows Updates", "hardware/check_updates.yml",
                "Busca actualizaciones de Windows pendientes sin instalar",
                action_type="read-only"
            ),
            MenuOption(
                "H10", "Auditoría General de Salud (Combo)", "hardware/health_audit.yml",
                "Ejecuta un diagnóstico completo: Specs, Batería, SMART y Updates",
                action_type="read-only"
            ),
            MenuOption(
                "H11", "Limpiar caché del sistema", "hardware/cleanup_cache.yml",
                "Elimina archivos temporales y caché del sistema",
                action_type="modify"
            ),
            MenuOption(
                "H12", "Limpiar perfiles de usuarios antiguos", "hardware/cleanup_old_users.yml",
                "Elimina perfiles de usuario que no se han usado en mucho tiempo",
                action_type="modify"
            ),
            MenuOption(
                "H13", "Recopilar logs del sistema", "hardware/collect_logs.yml",
                "Recopila y exporta logs de eventos de Windows",
                action_type="read-only"
            ),
            MenuOption(
                "H14", "Test de rendimiento", "hardware/performance_test.yml",
                "Ejecuta pruebas de rendimiento del sistema",
                action_type="read-only"
            ),
            MenuOption(
                "H15", "Inventario unificado", "hardware/unified_inventory.yml",
                "Genera un inventario completo del hardware y software",
                action_type="read-only"
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
                "Script WCORP + cleanDNS + gpupdate",
                action_type="modify"
            ),
            MenuOption(
                "R2", "Analizador Wi-Fi", "network/wifi_analyzer.yml",
                "Información detallada de conexión Wi-Fi, AP y señal",
                action_type="read-only"
            ),
            MenuOption(
                "R3", "Reparar red", "network/network_repair.yml",
                "Flush DNS, reset IP, reiniciar adaptador",
                action_type="modify"
            ),
            MenuOption(
                "R4", "Test de Velocidad", "network/speedtest.yml",
                "Test de velocidad de Internet (descarga, latencia, jitter)",
                action_type="read-only"
            ),
    
            MenuOption(
                "R6", "Resetear adaptador de red", "network/reset_adapter.yml",
                "Reinicia el adaptador de red especificado",
                action_type="modify"
            ),
            MenuOption(
                "R7", "Resolver nombre/IP", "network/resolve_host.yml",
                "Convierte IP a Hostname y viceversa",
                requires_input=True, input_prompt="IP o Hostname a resolver", input_var_name="target_host_dns",
                action_type="read-only", requires_hostname=False
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
                "Instalación silenciosa de Office 365",
                action_type="modify"
            ),
            MenuOption(
                "S2", "Reparar Office", "software/repair_office.yml",
                "Ejecuta Quick Repair de Office",
                action_type="modify"
            ),
            MenuOption(
                "S3", "Resetear OneDrive", "software/reset_onedrive.yml",
                "Resetea OneDrive a su configuración inicial",
                action_type="modify"
            ),
            MenuOption(
                "S4", "Listar aplicaciones instaladas", "software/list_apps.yml",
                "Exporta una lista completa del software instalado",
                action_type="read-only"
            ),
            MenuOption(
                "S5", "Desinstalar aplicación", "software/uninstall_app.yml",
                "Desinstala una aplicación específica del sistema",
                requires_input=True, input_prompt="Nombre de la aplicación a desinstalar", input_var_name="app_name",
                action_type="destructive", requires_hostname=True
            ),
            MenuOption(
                "S6", "Limpieza profunda de temporales", "software/deep_clean.yml",
                "Borra caché de Teams, Outlook y carpetas Temp del sistema",
                action_type="modify"
            ),
            MenuOption(
                "S7", "Detectar Shadow IT", "software/detect_shadow_it.yml",
                "Detecta aplicaciones instaladas sin autorización",
                action_type="read-only"
            ),
            MenuOption(
                "S8", "Instalar desde soporte", "software/install_from_support.yml",
                "Instala software desde ruta de soporte",
                action_type="modify"
            ),
            MenuOption(
                "S9", "Listar aplicaciones detallado", "software/list_apps_detailed.yml",
                "Lista completa de aplicaciones con detalles extendidos",
                action_type="read-only"
            ),
            MenuOption(
                "S10", "Gestionar servicios", "software/manage_services.yml",
                "Lista, inicia, detiene y configura servicios de Windows",
                action_type="modify"
            ),
            MenuOption(
                "S11", "Validar características de Windows", "software/validate_features.yml",
                "Verifica características y componentes instalados de Windows",
                action_type="read-only"
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
                "Gestión de spooler e impresoras",
                action_type="modify"
            ),
            MenuOption(
                "I2", "Calibrar Zebra", "printers/zebra_calibrate.yml",
                "Envía comando de calibración a impresora Zebra",
                requires_input=True, input_prompt="IP de la impresora Zebra", input_var_name="zebra_ip",
                action_type="modify", requires_hostname=False
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
                "Consola PowerShell interactiva",
                action_type="modify", can_new_window=True
            ),
            MenuOption(
                "C2", "Ejecutar comando/script custom", "remote/custom_command.yml",
                "Pega un comando PowerShell y ejecútalo remotamente",
                requires_input=True, input_prompt="Script PowerShell a ejecutar", input_var_name="custom_script",
                action_type="modify", can_background=False
            ),
        ]
    ),
    # =========================================================================
    # [SC] SCCM
    # =========================================================================
    MenuCategory(
        key="SC",
        name="SCCM",
        icon="🖥️",
        options=[
            MenuOption(
                "SC1", "Auditar clientes faltantes", "sccm/audit_missing_clients.yml",
                "Identifica equipos que no tienen el cliente SCCM instalado",
                action_type="read-only", requires_hostname=False
            ),
            MenuOption(
                "SC2", "Forzar actualización de políticas", "sccm/force_gpupdate.yml",
                "Fuerza la actualización de políticas de grupo en el equipo",
                action_type="modify"
            ),
            MenuOption(
                "SC3", "Estado del cliente SCCM", "sccm/get_client_status.yml",
                "Muestra el estado del cliente SCCM y sus servicios",
                action_type="read-only"
            ),
            MenuOption(
                "SC4", "Obtener colecciones", "sccm/get_collections.yml",
                "Lista las colecciones de SCCM a las que pertenece el equipo",
                action_type="read-only"
            ),
            MenuOption(
                "SC5", "Info del dispositivo en SCCM", "sccm/get_device_info.yml",
                "Muestra información detallada del dispositivo en SCCM",
                action_type="read-only"
            ),
            MenuOption(
                "SC6", "Listar dispositivos en SCCM", "sccm/list_devices.yml",
                "Lista todos los dispositivos gestionados por SCCM",
                action_type="read-only", requires_hostname=False
            ),
            MenuOption(
                "SC7", "Trigger acciones SCCM", "sccm/trigger_actions.yml",
                "Ejecuta acciones predefinidas del cliente SCCM",
                action_type="modify"
            ),
        ]
    ),
    # =========================================================================
    # [WL] WLC (Wireless Controller)
    # =========================================================================
    MenuCategory(
        key="WL",
        name="WLC",
        icon="📡",
        options=[
            MenuOption(
                "WL1", "Conectar a WLC", "wlc/connect_wlc.yml",
                "Establece conexión con el Wireless Controller",
                action_type="read-only", requires_hostname=False
            ),
            MenuOption(
                "WL2", "Generar reporte telecomunicaciones", "wlc/generate_telecom_report.yml",
                "Genera reporte completo de telecomunicaciones desde WLC",
                requires_input=True, input_prompt="IP o hostname del Wireless Controller", input_var_name="wlc_host",
                action_type="read-only", requires_hostname=False
            ),
            MenuOption(
                "WL3", "Info de cliente en WLC", "wlc/get_client_info.yml",
                "Muestra información de un cliente conectado a la red Wi-Fi",
                requires_input=True, input_prompt="MAC o IP del cliente", input_var_name="client_id",
                action_type="read-only", requires_hostname=False
            ),
            MenuOption(
                "WL4", "Buscar en WLC", "wlc/search_wlc.yml",
                "Busca dispositivos o información en el WLC",
                requires_input=True, input_prompt="Término de búsqueda", input_var_name="search_term",
                action_type="read-only", requires_hostname=False
            ),
            MenuOption(
                "WL5", "Mostrar clientes de AP", "wlc/show_ap_clients.yml",
                "Lista los clientes conectados a un Access Point",
                requires_input=True, input_prompt="Nombre del Access Point", input_var_name="ap_name",
                action_type="read-only", requires_hostname=False
            ),
            MenuOption(
                "WL6", "Listar Access Points", "wlc/show_ap_list.yml",
                "Lista todos los Access Points gestionados por el WLC",
                action_type="read-only", requires_hostname=False
            ),
        ]
    ),
    # =========================================================================
    # [M] MONITORING
    # =========================================================================
    MenuCategory(
        key="M",
        name="Monitoring",
        icon="📊",
        options=[
            MenuOption(
                "M1", "Recopilar métricas", "monitoring/collect_metrics.yml",
                "Recopila métricas de rendimiento y estado del sistema",
                action_type="read-only"
            ),
            MenuOption(
                "M2", "Health checks", "monitoring/health_checks.yml",
                "Ejecuta verificaciones de salud del sistema",
                action_type="read-only"
            ),
        ]
    ),
]
