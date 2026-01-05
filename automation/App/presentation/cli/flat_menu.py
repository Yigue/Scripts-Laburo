"""
CategoryMenu - Menú con categorías y submenús
Menú principal muestra categorías, al seleccionar una entra en submenú
"""
from typing import Callable, Dict, List, Optional
from .colors import Colors, ConsoleStyle
from utils.common import clear_screen

style = ConsoleStyle()


class MenuItem:
    """Representa un item del menú"""
    
    def __init__(self, num: int, label: str, action: Callable):
        self.num = num
        self.label = label
        self.action = action


class Category:
    """Representa una categoría del menú"""
    
    def __init__(self, key: str, name: str):
        self.key = key
        self.name = name
        self.items: List[MenuItem] = []
        self.current_num = 1
    
    def add_item(self, label: str, action: Callable):
        """Agrega un item a la categoría"""
        item = MenuItem(
            num=self.current_num,
            label=label,
            action=action
        )
        self.items.append(item)
        self.current_num += 1


class CategoryMenu:
    """
    Menú organizado por categorías con submenús
    Menú principal muestra categorías, al seleccionar entra en submenú
    """
    
    def __init__(self, title: str = "Menu Principal"):
        self.title = title
        self.categories: Dict[str, Category] = {}
        self.category_order: List[str] = []
    
    def add_category(self, key: str, name: str):
        """
        Agrega una nueva categoría
        
        Args:
            key: Letra de la categoría (ej: "H" para Hardware)
            name: Nombre de la categoría
        """
        cat = Category(key, name)
        self.categories[key] = cat
        self.category_order.append(key)
        return cat
    
    def add_item(self, category_key: str, label: str, action: Callable):
        """
        Agrega un item a una categoría existente
        
        Args:
            category_key: Letra de la categoría
            label: Etiqueta del item
            action: Función a ejecutar
        """
        if category_key in self.categories:
            cat = self.categories[category_key]
            cat.add_item(label, action)


class CategoryMenuRenderer:
    """
    Renderizador de menú con navegación por categorías
    - Menú principal: muestra categorías
    - Al seleccionar categoría: muestra submenú con opciones
    """
    
    def __init__(self, menu: CategoryMenu, hostname: str, executor, 
                 show_banner_func: Callable, show_welcome_func: Callable):
        self.menu = menu
        self.hostname = hostname
        self.executor = executor
        self.show_banner = show_banner_func
        self.show_welcome = show_welcome_func
        self.current_category: Optional[Category] = None
    
    def render_main_menu(self):
        """Renderiza el menú principal con las categorías"""
        clear_screen()
        self.show_banner()
        self.show_welcome(self.hostname)
        
        print()
        print(f"{Colors.BOLD}{Colors.WHITE}  SELECCIONA UNA CATEGORIA:{Colors.RESET}")
        print(f"{Colors.CYAN}  {'-' * 40}{Colors.RESET}")
        print()
        
        # Mostrar categorías en dos columnas
        cats = list(self.menu.categories.values())
        mid = (len(cats) + 1) // 2
        
        col_width = 38
        
        for i in range(mid):
            # Columna izquierda
            left_cat = cats[i]
            left_text = f"  {Colors.YELLOW}[{left_cat.key}]{Colors.RESET} {Colors.WHITE}{left_cat.name}{Colors.RESET}"
            left_len = len(f"  [{left_cat.key}] {left_cat.name}")
            
            # Columna derecha
            right_idx = i + mid
            if right_idx < len(cats):
                right_cat = cats[right_idx]
                right_text = f"  {Colors.YELLOW}[{right_cat.key}]{Colors.RESET} {Colors.WHITE}{right_cat.name}{Colors.RESET}"
            else:
                right_text = ""
            
            padding = col_width - left_len
            if padding < 2:
                padding = 2
            
            print(f"{left_text}{' ' * padding}{right_text}")
        
        print()
        print(f"{Colors.CYAN}  {'-' * 40}{Colors.RESET}")
        print()
        print(f"  {Colors.CYAN}[0]{Colors.RESET} {Colors.WHITE}Otro equipo{Colors.RESET}")
        print(f"  {Colors.RED}[X]{Colors.RESET} {Colors.WHITE}Salir{Colors.RESET}")
        print()
    
    def render_submenu(self, category: Category):
        """Renderiza el submenú de una categoría"""
        clear_screen()
        self.show_banner()
        
        print(f"{Colors.WHITE}                Equipo Remoto . . . . . : {Colors.YELLOW}{self.hostname}{Colors.RESET}")
        print()
        print(f"{Colors.CYAN}{'=' * 80}{Colors.RESET}")
        print()
        print(f"{Colors.BOLD}{Colors.CYAN}  [{category.key}] {category.name}{Colors.RESET}")
        print(f"{Colors.CYAN}  {'-' * 40}{Colors.RESET}")
        print()
        
        # Mostrar opciones de la categoría
        for item in category.items:
            print(f"  {Colors.YELLOW}{item.num}.{Colors.RESET} {Colors.WHITE}{item.label}{Colors.RESET}")
        
        print()
        print(f"{Colors.CYAN}  {'-' * 40}{Colors.RESET}")
        print()
        print(f"  {Colors.BLUE}[0]{Colors.RESET} {Colors.WHITE}<- Volver al menu principal{Colors.RESET}")
        print()
    
    def run(self):
        """Ejecuta el loop principal del menú"""
        while True:
            if self.current_category is None:
                # Mostrar menú principal
                result = self._run_main_menu()
                if result == "exit":
                    return "exit"
                elif result == "change_host":
                    return "change_host"
            else:
                # Mostrar submenú de categoría
                result = self._run_submenu()
                if result == "back":
                    self.current_category = None
    
    def _run_main_menu(self):
        """Ejecuta el menú principal"""
        while True:
            self.render_main_menu()
            
            opcion = input(f"{Colors.WHITE}Selecciona una opcion: {Colors.RESET}").strip().upper()
            
            if opcion == "0":
                return "change_host"
            
            if opcion == "X" or opcion == "Q":
                confirm = input(f"{Colors.YELLOW}Salir del programa? (S/N): {Colors.RESET}").strip().upper()
                if confirm == "S":
                    return "exit"
                continue
            
            # Buscar categoría
            if opcion in self.menu.categories:
                self.current_category = self.menu.categories[opcion]
                return "submenu"
            else:
                print(f"\n{style.error('Opcion invalida. Selecciona una letra de categoria.')}")
                input(f"{Colors.CYAN}Presiona ENTER para continuar...{Colors.RESET}")
    
    def _run_submenu(self):
        """Ejecuta el submenú de una categoría"""
        while True:
            self.render_submenu(self.current_category)
            
            opcion = input(f"{Colors.WHITE}Selecciona una opcion: {Colors.RESET}").strip()
            
            if opcion == "0":
                return "back"
            
            # Buscar opción numérica
            try:
                num = int(opcion)
                # Buscar item por número
                for item in self.current_category.items:
                    if item.num == num:
                        self._execute_action(item)
                        break
                else:
                    print(f"\n{style.error('Opcion invalida.')}")
                    input(f"{Colors.CYAN}Presiona ENTER para continuar...{Colors.RESET}")
            except ValueError:
                print(f"\n{style.error('Ingresa un numero valido.')}")
                input(f"{Colors.CYAN}Presiona ENTER para continuar...{Colors.RESET}")
    
    def _execute_action(self, item: MenuItem):
        """Ejecuta la acción de un item"""
        clear_screen()
        print(f"\n{Colors.CYAN}{'=' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}  Ejecutando: {Colors.WHITE}{item.label}{Colors.RESET}")
        print(f"{Colors.CYAN}{'=' * 70}{Colors.RESET}\n")
        
        try:
            item.action()
            print(f"\n{style.success(f'{item.label} completado.')}")
        except KeyboardInterrupt:
            print(f"\n{style.warning('Operacion cancelada por el usuario.')}")
        except Exception as e:
            print(f"\n{style.error(f'Error: {str(e)}')}")
        
        input(f"\n{Colors.CYAN}Presiona ENTER para volver al menu...{Colors.RESET}")


# Alias para compatibilidad
FlatMenu = CategoryMenu
FlatMenuRenderer = CategoryMenuRenderer

