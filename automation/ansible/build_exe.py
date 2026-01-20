# -*- coding: utf-8 -*-
"""
Script de construcción para generar ejecutable .exe con PyInstaller.

Uso:
    pip install pyinstaller
    python build_exe.py
"""

import os
import sys
from pathlib import Path

try:
    import PyInstaller.__main__
except ImportError:
    print("❌ PyInstaller no está instalado.")
    print("Instalar con: pip install pyinstaller")
    sys.exit(1)

# Directorio base del proyecto
BASE_DIR = Path(__file__).parent.absolute()

# Determinar separador de paths según OS
# En Windows PyInstaller usa ; para --add-data
# En Linux/Mac usa :
path_sep = ';' if sys.platform == 'win32' else ':'

# Verificar que los directorios existen
required_dirs = ['inventory', 'playbooks', 'roles']
for dir_name in required_dirs:
    if not (BASE_DIR / dir_name).exists():
        print(f"⚠️ Advertencia: {dir_name}/ no existe")

# Archivos de datos que PyInstaller debe incluir
datas = [
    ('inventory', 'inventory'),
    ('playbooks', 'playbooks'),
    ('roles', 'roles'),
    ('ansible.cfg', '.'),
]

# Archivos ocultos a incluir
hiddenimports = [
    'cli',
    'cli.domain',
    'cli.domain.models',
    'cli.domain.services',
    'cli.application',
    'cli.application.use_cases',
    'cli.application.validators',
    'cli.infrastructure',
    'cli.infrastructure.ansible',
    'cli.infrastructure.terminal',
    'cli.infrastructure.logging',
    'cli.presentation',
    'cli.presentation.cli',
    'cli.presentation.display',
    'cli.shared',
    'questionary',
    'rich',
    'rich.console',
    'rich.panel',
    'rich.table',
    'rich.progress',
    'rich.live',
    'rich.layout',
    'rich.align',
    'rich.box',
    'yaml',
    'prompt_toolkit',
    'wcwidth',
]

# Configuración de PyInstaller
pyinstaller_args = [
    'app.py',
    '--name=IT-Ops-CLI',
    '--onefile',  # Un solo archivo .exe
    # '--windowed',  # Sin consola (DESCOMENTAR si quieres ocultar la consola)
    '--clean',  # Limpiar archivos temporales
    '--noconfirm',  # Sobrescribir sin preguntar
    
    # Incluir archivos de datos (usar separador correcto para OS)
    *[f'--add-data={src}{path_sep}{dst}' for src, dst in datas],
    
    # Hidden imports
    *[f'--hidden-import={imp}' for imp in hiddenimports],
    
    # Opciones adicionales - recopilar todo de estas librerías
    '--collect-all', 'questionary',
    '--collect-all', 'rich',
    '--collect-all', 'yaml',
    '--collect-all', 'prompt_toolkit',
    '--collect-submodules', 'cli',
    
    # Excluir módulos innecesarios para reducir tamaño
    '--exclude-module', 'matplotlib',
    '--exclude-module', 'numpy',
    '--exclude-module', 'pandas',
    '--exclude-module', 'tkinter',
    '--exclude-module', 'PyQt5',
    '--exclude-module', 'PyQt6',
    '--exclude-module', 'IPython',
    '--exclude-module', 'jupyter',
]

if __name__ == '__main__':
    os.chdir(BASE_DIR)
    print(f"📦 Construyendo ejecutable desde: {BASE_DIR}")
    print("⏳ Esto puede tomar varios minutos...")
    print(f"📋 Modo: {'Windows' if sys.platform == 'win32' else 'Linux/Mac'}")
    print(f"🔗 Separador de paths: {path_sep}")
    print()
    
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("\n" + "="*60)
        print("✅ Ejecutable creado exitosamente!")
        print("="*60)
        print(f"📁 Ubicación: {BASE_DIR / 'dist' / 'IT-Ops-CLI.exe'}")
        print()
        print("📝 Notas:")
        print("  - El ejecutable es autocontenido")
        print("  - Requiere Ansible instalado en el sistema destino")
        print("  - El archivo vault.yml NO está incluido por seguridad")
        print("  - Prueba el ejecutable antes de distribuir")
        print()
    except Exception as e:
        print(f"\n❌ Error durante la construcción: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
