# -*- mode: python ; coding: utf-8 -*-
"""
Archivo de especificación de PyInstaller para IT-Ops CLI.

Este archivo permite personalizar la construcción del .exe

Uso:
    pyinstaller IT-Ops-CLI.spec
"""

import os
from pathlib import Path

block_cipher = None

# Directorio base
BASE_DIR = Path(SPECPATH).parent

# Archivos de datos
datas = [
    (str(BASE_DIR / 'inventory'), 'inventory'),
    (str(BASE_DIR / 'playbooks'), 'playbooks'),
    (str(BASE_DIR / 'roles'), 'roles'),
    (str(BASE_DIR / 'ansible.cfg'), '.'),
]

# Hidden imports
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
    'yaml',
]

a = Analysis(
    [str(BASE_DIR / 'app.py')],
    pathex=[str(BASE_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'tkinter', 'PyQt5', 'PyQt6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='IT-Ops-CLI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Cambiar a False para ocultar consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
