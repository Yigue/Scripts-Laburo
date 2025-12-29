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
    Carga configuración desde archivo JSON
    Busca en la raíz del proyecto (donde está el README.md)
    
    Args:
        config_file: Nombre del archivo de configuración
    
    Returns:
        dict: Configuración cargada o valores por defecto
    """
    default_config = {
        "psexec_path": "PsExec.exe",
        "remote_user": "Administrador",
        "remote_pass": "",
        "timeout": 30
    }
    
    # Buscar config.json en la raíz del proyecto
    # Asumimos que la raíz tiene README.md o está 2-3 niveles arriba
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = current_dir
    for _ in range(3):  # Buscar hasta 3 niveles arriba
        config_path = os.path.join(project_root, config_file)
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                break
            except Exception as e:
                print(f"⚠ Error cargando configuración: {e}")
                break
        project_root = os.path.dirname(project_root)
    
    return default_config


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

