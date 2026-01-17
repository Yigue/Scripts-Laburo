# -*- coding: utf-8 -*-
"""
cli/config.py
=============
Configuración global de la aplicación.

Contiene:
- BASE_DIR: Directorio base del proyecto
- logger: Logger configurado
- console: Instancia de Rich Console
- CUSTOM_STYLE: Estilo personalizado para Questionary
"""

import os
import sys
import logging
from pathlib import Path

# Verificar dependencias
try:
    from questionary import Style
    from rich.console import Console
except ImportError as e:
    print(f"Error: Falta dependencia - {e}")
    print("Ejecutar: pip install -r requirements.txt")
    sys.exit(1)

# Directorio base del proyecto (un nivel arriba de cli/)
BASE_DIR = Path(__file__).parent.parent.absolute()
os.chdir(BASE_DIR)

# Crear directorios necesarios
(BASE_DIR / "logs").mkdir(exist_ok=True)
(BASE_DIR / "reports").mkdir(exist_ok=True)
(BASE_DIR / ".cache").mkdir(exist_ok=True)

# Configurar logging
logging.basicConfig(
    filename=BASE_DIR / "logs" / "cli_execution.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Consola Rich global con soporte para grabación HTML
console = Console(record=True, width=120)

# Estilo personalizado para Questionary
CUSTOM_STYLE = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:white bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:cyan bold'),
    ('selected', 'fg:green'),
    ('separator', 'fg:gray'),
    ('instruction', 'fg:gray'),
])
