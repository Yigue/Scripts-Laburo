"""
MenuBuilder - Constructor de menús
Patrón Builder para crear menús complejos
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class MenuItem:
    """Representa un item de menú"""
    key: str
    label: str
    action: Optional[Callable] = None
    submenu: Optional['Menu'] = None
    description: str = ""
    require_confirmation: bool = False
    
    @property
    def is_submenu(self) -> bool:
        """Verifica si el item es un submenú"""
        return self.submenu is not None


@dataclass
class Menu:
    """Representa un menú completo"""
    title: str
    items: Dict[str, MenuItem] = field(default_factory=dict)
    parent: Optional['Menu'] = None
    
    def add_item(self, key: str, label: str, action: Callable, 
                 description: str = "", require_confirmation: bool = False):
        """
        Agrega un item al menú
        
        Args:
            key: Tecla para seleccionar el item
            label: Etiqueta a mostrar
            action: Función a ejecutar
            description: Descripción del item
            require_confirmation: Si requiere confirmación antes de ejecutar
        """
        self.items[key.upper()] = MenuItem(
            key=key.upper(),
            label=label,
            action=action,
            description=description,
            require_confirmation=require_confirmation
        )
    
    def add_submenu(self, key: str, label: str, submenu: 'Menu'):
        """
        Agrega un submenú
        
        Args:
            key: Tecla para acceder al submenú
            label: Etiqueta del submenú
            submenu: Instancia del submenú
        """
        submenu.parent = self
        self.items[key.upper()] = MenuItem(
            key=key.upper(),
            label=label,
            submenu=submenu
        )
    
    def get_item(self, key: str) -> Optional[MenuItem]:
        """Obtiene un item por su clave"""
        return self.items.get(key.upper())
    
    def has_parent(self) -> bool:
        """Verifica si el menú tiene padre"""
        return self.parent is not None


class MenuBuilder:
    """
    Constructor fluido de menús
    Implementa Builder Pattern
    """
    
    def __init__(self, title: str = "Menú Principal"):
        """
        Inicializa el builder
        
        Args:
            title: Título del menú
        """
        self._menu = Menu(title=title)
    
    def add_action(self, key: str, label: str, action: Callable, 
                  description: str = "", require_confirmation: bool = False):
        """Agrega una acción al menú"""
        self._menu.add_item(key, label, action, description, require_confirmation)
        return self
    
    def add_submenu(self, key: str, label: str, submenu: Menu):
        """Agrega un submenú"""
        self._menu.add_submenu(key, label, submenu)
        return self
    
    def build(self) -> Menu:
        """Construye y retorna el menú"""
        return self._menu


def create_category_menu(title: str, actions: Dict[str, tuple]) -> Menu:
    """
    Helper para crear menús de categoría rápidamente
    
    Args:
        title: Título del menú
        actions: Dict de {key: (label, action, [description])}
        
    Returns:
        Menu creado
        
    Example:
        menu = create_category_menu("Hardware", {
            "1": ("Info del sistema", system_info.ejecutar),
            "2": ("Configurar equipo", configurar_equipo.ejecutar, "30-60 min")
        })
    """
    menu = Menu(title=title)
    
    for key, value in actions.items():
        if len(value) >= 2:
            label, action = value[0], value[1]
            description = value[2] if len(value) > 2 else ""
            menu.add_item(key, label, action, description)
    
    return menu

