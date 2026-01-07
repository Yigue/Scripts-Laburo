"""
Utilidades comunes para los scripts de automatización
"""
import json
import os
import getpass
from datetime import datetime


def save_report(data, filename, output_dir="data/reports"):
    """
    Guarda un reporte en formato JSON
    
    Args:
        data: Datos a guardar (dict o list)
        filename: Nombre del archivo (sin extensión)
        output_dir: Directorio de salida
    
    Returns:
        str: Ruta completa del archivo guardado
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    return filepath


def load_config(config_file="config.json"):
    """
    Carga configuración utilizando AppConfig central
    Manteniene compatibilidad retornando dict
    """
    # Importar aquí para evitar circular imports si config importa utils
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    try:
        from config import get_config
        conf = get_config()

        return {
            "psexec_path": conf.psexec_path,
            "remote_user": conf.remote_user or "Administrador",
            "remote_pass": conf.remote_pass or "",
            "timeout": conf.default_timeout,
            "log_dir": conf.log_dir
        }
    except ImportError:
        # Fallback por si falla el import path hack
        return {
            "psexec_path": "PsExec.exe",
            "remote_user": "Administrador",
            "remote_pass": "",
            "timeout": 30
        }


def clear_screen():
    """Limpia la pantalla (cross-platform)"""
    os.system("cls" if os.name == "nt" else "clear")


def format_size(size_bytes):
    """Formatea bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_credentials(default_user="Administrador", prompt_user=True):
    """
    Solicita credenciales de administrador al usuario
    
    Args:
        default_user: Usuario por defecto
        prompt_user: Si True, pregunta por el usuario; si False, usa el default
    
    Returns:
        tuple: (usuario, contraseña)
    """
    print("\n🔐 Credenciales de Administrador")
    print("-" * 40)
    
    if prompt_user:
        user = input(f"Usuario [{default_user}]: ").strip()
        if not user:
            user = default_user
    else:
        user = default_user
        print(f"Usuario: {user}")
    
    # Usar getpass para ocultar la contraseña
    try:
        password = getpass.getpass("Contraseña: ")
    except Exception:
        # Fallback si getpass no funciona (ej: en algunos IDEs)
        password = input("Contraseña: ")
    
    if not password:
        print("⚠️  Contraseña vacía - algunas operaciones pueden fallar")
    
    return user, password


def get_credentials_cached():
    """
    Solicita credenciales y las guarda en memoria para la sesión actual
    No guarda en disco por seguridad
    
    Returns:
        tuple: (usuario, contraseña)
    """
    if not hasattr(get_credentials_cached, '_cached'):
        get_credentials_cached._cached = None
    
    if get_credentials_cached._cached is None:
        get_credentials_cached._cached = get_credentials()
    else:
        print(f"\n🔐 Usando credenciales en caché (Usuario: {get_credentials_cached._cached[0]})")
        cambiar = input("¿Cambiar credenciales? (S/N) [N]: ").strip().upper()
        if cambiar == "S":
            get_credentials_cached._cached = get_credentials()
    
    return get_credentials_cached._cached


def clear_cached_credentials():
    """Limpia las credenciales en caché"""
    if hasattr(get_credentials_cached, '_cached'):
        get_credentials_cached._cached = None
        print("🔐 Credenciales en caché eliminadas")


def log_result(operation, hostname, success, details="", log_dir="data/logs"):
    """
    Guarda un log de operación
    
    Args:
        operation: Nombre de la operación (ej: "onedrive_fix")
        hostname: Hostname del equipo
        success: True si fue exitoso
        details: Detalles adicionales
        log_dir: Directorio de logs
    """
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{operation}_{datetime.now().strftime('%Y%m%d')}.log")
    
    status = "SUCCESS" if success else "FAILED"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {status} - {hostname} - {details}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
