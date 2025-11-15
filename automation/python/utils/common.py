"""
Utilidades comunes para los scripts de automatización
"""
import json
import os
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

