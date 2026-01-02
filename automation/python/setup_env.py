"""
Script de ayuda para configurar el archivo .env
"""
import os
import sys
import shutil
from pathlib import Path

# Configurar encoding para Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def setup_env():
    """Crea el archivo .env desde .env.example si no existe"""
    # Buscar la raíz del proyecto
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent  # Subir hasta Scripts-Laburo/
    
    env_example = project_root / ".env.example"
    env_file = project_root / ".env"
    
    print("=" * 60)
    print("CONFIGURACION DE VARIABLES DE ENTORNO")
    print("=" * 60)
    print()
    
    if not env_example.exists():
        print("[ERROR] No se encontro .env.example")
        print(f"   Buscado en: {env_example}")
        return
    
    if env_file.exists():
        print(f"[OK] El archivo .env ya existe en: {env_file}")
        respuesta = input("\nQueres sobrescribirlo? (S/N): ").strip().upper()
        if respuesta != "S":
            print("[OK] Manteniendo el archivo .env existente")
            return
    
    # Copiar .env.example a .env
    try:
        shutil.copy(env_example, env_file)
        print(f"[OK] Archivo .env creado en: {env_file}")
        print()
        print("Ahora edita el archivo .env y completa tus credenciales:")
        print(f"   {env_file}")
        print()
        print("Variables importantes a configurar:")
        print("   - WINRM_USER o PSEXEC_USER")
        print("   - WINRM_PASS o PSEXEC_PASS")
        print("   - WINRM_DOMAIN o PSEXEC_DOMAIN (opcional)")
        print()
        print("Tip: Podes usar las mismas credenciales para WinRM y PsExec")
        print("   Solo configura WINRM_USER/WINRM_PASS y PsExec las usara automaticamente")
        
    except Exception as e:
        print(f"[ERROR] Error creando .env: {e}")

if __name__ == "__main__":
    setup_env()

