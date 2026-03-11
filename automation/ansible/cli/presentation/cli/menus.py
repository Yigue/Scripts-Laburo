# -*- coding: utf-8 -*-
"""
presentation/cli/menus.py
=========================
Funciones de navegación de menú.

Contiene funciones para mostrar y navegar por las categorías y opciones del menú.
La ejecución de opciones se delega a menu_handler.py
"""

from typing import Optional
import questionary

from ...shared.config import CUSTOM_STYLE
from ...domain.models import MenuOption, MenuCategory
# Importar MENU_CATEGORIES desde cli (exportado en __init__.py)
try:
    from cli import MENU_CATEGORIES
except ImportError:
    # Fallback: importar directamente
    from cli.menu_data import MENU_CATEGORIES


def mostrar_menu_categorias() -> Optional[MenuCategory]:
    """
    Muestra el menú de categorías con navegación por letras/números.
    
    Returns:
        MenuCategory: La categoría seleccionada, o None si cancela/sale
    """
    # Preparar opciones con claves visibles para navegación rápida
    choices = []
    used_shortcuts = set()
    
    # Mapeo de categorías a atajos únicos
    category_shortcuts = {
        "A": "a",  # Admin
        "H": "h",  # Hardware
        "R": "r",  # Redes
        "S": "s",  # Software
        "I": "i",  # Impresoras
        "C": "c",  # Consola
        "SC": "1",  # SCCM (usar número para evitar conflicto)
        "WL": "2",  # WLC (usar número para evitar conflicto)
        "M": "m",  # Monitoring
    }
    
    for cat in MENU_CATEGORIES:
        shortcut = category_shortcuts.get(cat.key, None)
        if shortcut and shortcut not in used_shortcuts:
            choices.append(questionary.Choice(
                title=f"[{shortcut.upper()}] {cat.icon} {cat.name}",
                value=cat,
                shortcut_key=shortcut
            ))
            used_shortcuts.add(shortcut)
        else:
            # Si no hay shortcut disponible, no usar atajo
            choices.append(f"{cat.icon} {cat.name}")
    
    choices.append(questionary.Separator())
    # Historial usa "H" pero ya está usado por Hardware, usar "0" o letra alternativa
    choices.append(questionary.Choice(
        title="[0] 📜 Historial",
        value="HI",
        shortcut_key="0"
    ))
    choices.append(questionary.Choice(
        title="[D] 📊 Dashboard",
        value="D",
        shortcut_key="d"
    ))
    choices.append(questionary.Choice(
        title="[Q] ❌ Salir",
        value=None,
        shortcut_key="q"
    ))
    
    answer = questionary.select(
        "Seleccione una opción (usa letras/números para navegar rápido):",
        choices=choices,
        style=CUSTOM_STYLE,
        use_indicator=True,
        use_shortcuts=True
    ).ask()
    
    if answer is None or answer == "HI" or answer == "D":
        # Manejar respuestas especiales
        if answer == "HI":
            return MenuCategory(key="HI", name="Historial", icon="📜", options=[])
        elif answer == "D":
            return MenuCategory(key="D", name="Dashboard", icon="📊", options=[])
        return None
    
    # Si la respuesta es una categoría, retornarla directamente
    if isinstance(answer, MenuCategory):
        return answer
    
    # Fallback: buscar por nombre
    for cat in MENU_CATEGORIES:
        if hasattr(answer, 'name') and cat.name == answer.name:
            return cat
        elif isinstance(answer, str) and (cat.name in answer or cat.icon in answer):
            return cat
    
    return None


def mostrar_menu_opciones(categoria: MenuCategory) -> Optional[MenuOption]:
    """
    Muestra las opciones de una categoría con navegación por números.
    
    Args:
        categoria: La categoría cuyas opciones mostrar
        
    Returns:
        MenuOption: La opción seleccionada, o None si vuelve atrás
    """
    choices = []
    
    # Agregar opciones con números como atajos (1-9, luego letras si es necesario)
    shortcut_keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
    
    for idx, opt in enumerate(categoria.options):
        # Mostrar solo el label sin prefijo de clave
        display_label = opt.label
        
        # Asignar atajo numérico para las primeras 9 opciones
        if idx < 9:
            shortcut = shortcut_keys[idx]
            choices.append(questionary.Choice(
                title=display_label,
                value=opt,
                shortcut_key=shortcut
            ))
        else:
            # Para más de 9 opciones, mostrar solo el label sin número
            choices.append(questionary.Choice(
                title=opt.label,
                value=opt
            ))
    
    choices.append(questionary.Separator())
    choices.append(questionary.Choice(
        title="[V] ← Volver",
        value=None,
        shortcut_key="v"
    ))
    
    answer = questionary.select(
        f"{categoria.icon} {categoria.name}",
        choices=choices,
        style=CUSTOM_STYLE,
        use_indicator=True,
        use_shortcuts=True
    ).ask()
    
    if answer is None:
        return None
    
    # Si la respuesta es una opción, retornarla directamente
    if isinstance(answer, MenuOption):
        return answer
    
    # Fallback: buscar por label
    if isinstance(answer, str):
        for opt in categoria.options:
            if opt.label in answer or opt.key in answer:
                return opt
    
    return None
