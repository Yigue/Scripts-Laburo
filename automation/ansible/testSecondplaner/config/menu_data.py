"""
Configuración de menús y datos de playbooks con metadatos
"""
from typing import List, Tuple, Dict, Any

# Tipo de acción: read-only (sin confirmación), modify (confirmación simple), destructive (confirmación doble)
ACTION_TYPES = {
    "read-only": "read-only",
    "modify": "modify",
    "destructive": "destructive"
}

# Definición de menú principal con metadatos
MENU_DATA: Dict[str, List[Dict[str, Any]]] = {
    "🔐 Active Directory": [
        {
            "name": "Listar Usuarios",
            "playbook": "playbooks/admin/list_ad_users.yml",
            "action_type": "read-only",
            "requires_target": False,
            "requires_user": False,
            "impact_description": "Lista usuarios de Active Directory"
        },
        {
            "name": "Auditar Inactivos",
            "playbook": "playbooks/admin/audit_inactive.yml",
            "action_type": "read-only",
            "requires_target": False,
            "requires_user": False,
            "impact_description": "Audita usuarios inactivos en AD"
        },
        {
            "name": "Miembros de Grupo",
            "playbook": "playbooks/admin/get_group_members.yml",
            "action_type": "read-only",
            "requires_target": False,
            "requires_user": False,
            "impact_description": "Lista miembros de un grupo de AD"
        },
        {
            "name": "Desbloquear Usuario",
            "playbook": "playbooks/admin/unlock_user.yml",
            "action_type": "modify",
            "requires_target": False,
            "requires_user": True,
            "impact_description": "Desbloquea cuenta de usuario en AD"
        },
        {
            "name": "Obtener LAPS Password",
            "playbook": "playbooks/admin/get_laps_password.yml",
            "action_type": "read-only",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Obtiene password LAPS de un equipo"
        },
    ],
    "💻 Hardware": [
        {
            "name": "Test de Performance",
            "playbook": "playbooks/hardware/performance_test.yml",
            "action_type": "read-only",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Ejecuta test de performance del hardware"
        },
        {
            "name": "Inventario Unificado",
            "playbook": "playbooks/hardware/unified_inventory.yml",
            "action_type": "read-only",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Genera inventario unificado del hardware"
        },
        {
            "name": "Recolección de Logs",
            "playbook": "playbooks/hardware/collect_logs.yml",
            "action_type": "read-only",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Recopila logs del sistema"
        },
        {
            "name": "Especificaciones",
            "playbook": "playbooks/hardware/specs.yml",
            "action_type": "read-only",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Muestra especificaciones del hardware"
        },
        {
            "name": "Salud de Batería",
            "playbook": "playbooks/hardware/battery_health.yml",
            "action_type": "read-only",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Verifica salud de la batería"
        },
    ],
    "📶 Red y WIFI": [
        {
            "name": "Resetear Adaptador WIFI",
            "playbook": "playbooks/network/reset_adapter.yml",
            "action_type": "modify",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Resetea el adaptador WiFi (pérdida temporal de conexión)"
        },
        {
            "name": "WiFi Analyzer",
            "playbook": "playbooks/network/wifi_analyzer.yml",
            "action_type": "read-only",
            "requires_target": False,  # Puede ser local
            "requires_user": False,
            "impact_description": "Analiza redes WiFi disponibles"
        },
        {
            "name": "Network Repair",
            "playbook": "playbooks/network/network_repair.yml",
            "action_type": "modify",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Repara configuración de red"
        },
        {
            "name": "WCORP Fix",
            "playbook": "playbooks/network/wcorp_fix.yml",
            "action_type": "modify",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Corrige problemas de conexión WCORP"
        },
    ],
    "📦 Software": [
        {
            "name": "Listar Apps Detallado",
            "playbook": "playbooks/software/list_apps_detailed.yml",
            "action_type": "read-only",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Lista aplicaciones instaladas"
        },
        {
            "name": "Detectar Shadow IT",
            "playbook": "playbooks/software/detect_shadow_it.yml",
            "action_type": "read-only",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Detecta software no autorizado"
        },
        {
            "name": "Instalar Office",
            "playbook": "playbooks/software/install_office.yml",
            "action_type": "modify",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Instala Microsoft Office"
        },
        {
            "name": "Reparar Office",
            "playbook": "playbooks/software/repair_office.yml",
            "action_type": "modify",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Repara instalación de Office"
        },
        {
            "name": "Reset OneDrive",
            "playbook": "playbooks/software/reset_onedrive.yml",
            "action_type": "modify",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Resetea configuración de OneDrive"
        },
    ],
    "🖨️ Impresoras": [
        {
            "name": "Gestionar Impresoras",
            "playbook": "playbooks/printers/manage_printers.yml",
            "action_type": "modify",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Gestiona impresoras instaladas"
        },
        {
            "name": "Calibrar Zebra",
            "playbook": "playbooks/printers/zebra_calibrate.yml",
            "action_type": "modify",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Calibra impresora Zebra"
        },
    ],
    "🌐 WLC Cisco": [
        {
            "name": "Ver Lista de APs",
            "playbook": "playbooks/wlc/show_ap_list.yml",
            "action_type": "read-only",
            "requires_target": False,
            "requires_user": False,
            "requires_wlc_profile": True,
            "impact_description": "Muestra lista de Access Points"
        },
        {
            "name": "Reporte Telecom",
            "playbook": "playbooks/wlc/generate_telecom_report.yml",
            "action_type": "read-only",
            "requires_target": False,
            "requires_user": False,
            "requires_wlc_profile": True,
            "impact_description": "Genera reporte para telecomunicaciones"
        },
        {
            "name": "Clientes AP",
            "playbook": "playbooks/wlc/show_ap_clients.yml",
            "action_type": "read-only",
            "requires_target": False,
            "requires_user": False,
            "requires_wlc_profile": True,
            "impact_description": "Muestra clientes conectados a un AP"
        },
    ],
    "📊 SCCM": [
        {
            "name": "Listar Dispositivos",
            "playbook": "playbooks/sccm/list_devices.yml",
            "action_type": "read-only",
            "requires_target": False,
            "requires_user": False,
            "impact_description": "Lista dispositivos en SCCM"
        },
        {
            "name": "Estado Cliente",
            "playbook": "playbooks/sccm/get_client_status.yml",
            "action_type": "read-only",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Verifica estado del cliente SCCM"
        },
        {
            "name": "Forzar GPUpdate",
            "playbook": "playbooks/sccm/force_gpupdate.yml",
            "action_type": "modify",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Fuerza actualización de políticas de grupo"
        },
    ],
    "🔧 Monitoreo": [
        {
            "name": "Health Checks",
            "playbook": "playbooks/monitoring/health_checks.yml",
            "action_type": "read-only",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Ejecuta health checks del sistema"
        },
        {
            "name": "Recopilar Métricas",
            "playbook": "playbooks/monitoring/collect_metrics.yml",
            "action_type": "read-only",
            "requires_target": True,
            "requires_user": False,
            "impact_description": "Recopila métricas del sistema"
        },
    ],
}
