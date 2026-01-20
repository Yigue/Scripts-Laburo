# -*- coding: utf-8 -*-
"""
presentation/display/utils.py
==============================
Utilidades de visualización.

Funciones auxiliares para limpiar pantalla y mostrar banner.
"""

import os

from ...shared.config import console


def clear_screen():
    """Limpia la pantalla del terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_banner():
    """Muestra el banner minimalista."""
    console.print("[cyan bold]IT-OPS CLI[/cyan bold] [dim]| Automatización IT con Ansible[/dim]\n")


def show_menu_summary():
    """Muestra un resumen minimalista de las categorías disponibles."""
    # Versión minimalista - solo mostrar en una línea simple si es necesario
    pass  # Se omite para diseño minimalista
