"""
Definición de comandos CLI para modo rápido
"""
import argparse
from typing import List, Dict, Any


def build_cli_parser() -> argparse.ArgumentParser:
    """Construir parser de argumentos CLI"""
    parser = argparse.ArgumentParser(
        prog="itops",
        description="IT-Ops Automation Hub - Modo CLI rápido"
    )
    
    # Subparsers por módulo
    subparsers = parser.add_subparsers(dest="module", help="Módulo de operación")
    
    # Módulo: windows
    windows_parser = subparsers.add_parser("windows", help="Operaciones Windows/Software")
    windows_sub = windows_parser.add_subparsers(dest="action")
    
    apps_parser = windows_sub.add_parser("apps", help="Gestionar aplicaciones")
    apps_parser.add_argument("action_app", choices=["list", "install", "uninstall"])
    apps_parser.add_argument("--host", help="Hostname/IP del target")
    apps_parser.add_argument("--app", help="Nombre de la aplicación")
    apps_parser.add_argument("--json", action="store_true", help="Salida en JSON")
    
    # Módulo: ad
    ad_parser = subparsers.add_parser("ad", help="Operaciones Active Directory")
    ad_sub = ad_parser.add_subparsers(dest="action")
    
    unlock_parser = ad_sub.add_parser("unlock", help="Desbloquear usuario")
    unlock_parser.add_argument("--user", required=True, help="Username a desbloquear")
    unlock_parser.add_argument("--json", action="store_true", help="Salida en JSON")
    
    laps_parser = ad_sub.add_parser("laps", help="Obtener password LAPS")
    laps_parser.add_argument("--host", required=True, help="Hostname/IP del target")
    laps_parser.add_argument("--json", action="store_true", help="Salida en JSON")
    
    # Módulo: hardware
    hardware_parser = subparsers.add_parser("hardware", help="Operaciones Hardware")
    hardware_sub = hardware_parser.add_subparsers(dest="action")
    
    specs_parser = hardware_sub.add_parser("specs", help="Obtener especificaciones")
    specs_parser.add_argument("--host", required=True, help="Hostname/IP del target")
    specs_parser.add_argument("--json", action="store_true", help="Salida en JSON")
    
    battery_parser = hardware_sub.add_parser("battery", help="Verificar batería")
    battery_parser.add_argument("--host", required=True, help="Hostname/IP del target")
    battery_parser.add_argument("--json", action="store_true", help="Salida en JSON")
    
    # Módulo: sccm
    sccm_parser = subparsers.add_parser("sccm", help="Operaciones SCCM")
    sccm_sub = sccm_parser.add_subparsers(dest="action")
    
    status_parser = sccm_sub.add_parser("status", help="Estado del cliente SCCM")
    status_parser.add_argument("--host", required=True, help="Hostname/IP del target")
    status_parser.add_argument("--json", action="store_true", help="Salida en JSON")
    
    gpupdate_parser = sccm_sub.add_parser("gpupdate", help="Forzar GPUpdate")
    gpupdate_parser.add_argument("--host", required=True, help="Hostname/IP del target")
    gpupdate_parser.add_argument("--json", action="store_true", help="Salida en JSON")
    
    # Módulo: network
    network_parser = subparsers.add_parser("network", help="Operaciones Network")
    network_sub = network_parser.add_subparsers(dest="action")
    
    wifi_parser = network_sub.add_parser("wifi", help="Analizar WiFi")
    wifi_parser.add_argument("--local", action="store_true", help="Analizar localmente")
    wifi_parser.add_argument("--host", help="Hostname/IP del target (si no es local)")
    wifi_parser.add_argument("--json", action="store_true", help="Salida en JSON")
    
    # Flags globales
    parser.add_argument("--check", action="store_true", help="Modo check (simulación)")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Aumentar verbosity")
    parser.add_argument("--read-only", action="store_true", help="Forzar modo read-only")
    
    return parser


def parse_action(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Convertir argumentos parseados en acción ejecutable
    
    Returns:
        Diccionario con información de la acción a ejecutar
    """
    action_map = {
        ("windows", "apps", "list"): {
            "playbook": "playbooks/software/list_apps_detailed.yml",
            "requires_target": True,
            "action_type": "read-only"
        },
        ("windows", "apps", "install"): {
            "playbook": "playbooks/software/install_office.yml",  # Simplificado
            "requires_target": True,
            "action_type": "modify"
        },
        ("ad", "unlock"): {
            "playbook": "playbooks/admin/unlock_user.yml",
            "requires_target": False,
            "requires_user": True,
            "action_type": "modify"
        },
        ("ad", "laps"): {
            "playbook": "playbooks/admin/get_laps_password.yml",
            "requires_target": True,
            "action_type": "read-only"
        },
        ("hardware", "specs"): {
            "playbook": "playbooks/hardware/specs.yml",
            "requires_target": True,
            "action_type": "read-only"
        },
        ("hardware", "battery"): {
            "playbook": "playbooks/hardware/battery_health.yml",
            "requires_target": True,
            "action_type": "read-only"
        },
        ("sccm", "status"): {
            "playbook": "playbooks/sccm/get_client_status.yml",
            "requires_target": True,
            "action_type": "read-only"
        },
        ("sccm", "gpupdate"): {
            "playbook": "playbooks/sccm/force_gpupdate.yml",
            "requires_target": True,
            "action_type": "modify"
        },
        ("network", "wifi"): {
            "playbook": "playbooks/network/wifi_analyzer.yml",
            "requires_target": False,
            "action_type": "read-only"
        },
    }
    
    # Construir clave según los argumentos disponibles
    action_app = getattr(args, "action_app", None)
    if action_app:
        key = (args.module, args.action, action_app)
    else:
        key = (args.module, args.action)
    
    if key not in action_map:
        return None
    
    result = action_map[key].copy()
    result["extra_vars"] = {}
    
    # Agregar parámetros según los argumentos
    if hasattr(args, "host") and args.host:
        result["target"] = args.host
    if hasattr(args, "user") and args.user:
        result["extra_vars"]["username"] = args.user
    
    # Flags globales
    if hasattr(args, "check") and args.check:
        result["extra_vars"]["check_mode"] = True
    if hasattr(args, "verbose") and args.verbose:
        result["extra_vars"]["verbosity"] = min(args.verbose, 4)
    
    result["output_json"] = getattr(args, "json", False)
    result["read_only"] = getattr(args, "read_only", False)
    
    return result
