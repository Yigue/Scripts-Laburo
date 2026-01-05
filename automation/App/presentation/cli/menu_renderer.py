"""
MenuRenderer - Renderizador de menús mejorado
Muestra menús en consola y maneja la navegación
Con soporte completo de colores, breadcrumbs y ayuda
"""
from typing import Optional
from colorama import Fore, Back, Style, init
from .menu_builder import Menu, MenuItem
from .colors import Colors, ConsoleStyle
from utils.common import clear_screen

init(autoreset=True)  # Init colorama

style = ConsoleStyle()


class MenuRenderer:
    """
    Renderizador de menús para consola
    Maneja la visualización y navegación de menús
    """
    
    def __init__(self, root_menu: Menu, context: dict = None):
        """
        Inicializa el renderer
        
        Args:
            root_menu: Menú raíz
            context: Contexto compartido entre menús (ej: hostname, executor)
        """
        self.root_menu = root_menu
        self.current_menu = root_menu
        self.context = context or {}
        self.breadcrumbs: list = []
    
    def render(self, menu: Optional[Menu] = None):
        """
        Renderiza un menú en consola con diseño mejorado
        
        Args:
            menu: Menú a renderizar (usa current_menu si no se especifica)
        """
        if menu is None:
            menu = self.current_menu
        
        clear_screen()
        
        # Header con hostname
        if 'hostname' in self.context:
            hostname = self.context['hostname']
            print(f"{Colors.CYAN}+{'=' * 70}+{Colors.RESET}")
            print(f"{Colors.CYAN}|{Colors.RESET}  {Colors.BOLD}{Colors.GREEN}[*] Equipo:{Colors.RESET} {Colors.WHITE}{hostname:55}{Colors.RESET}  {Colors.CYAN}|{Colors.RESET}")
            print(f"{Colors.CYAN}+{'=' * 70}+{Colors.RESET}\n")
        
        # Mostrar breadcrumbs si no es el menú raíz
        if self.breadcrumbs:
            breadcrumb_str = " > ".join(self.breadcrumbs + [menu.title])
            print(f"{Colors.DIM}{Colors.CYAN}[>] {breadcrumb_str}{Colors.RESET}\n")
        
        # Título del menú con estilo mejorado
        title_width = 70
        title_padding = (title_width - len(menu.title) - 2) // 2
        print(f"{Colors.BG_BLUE}{Colors.BOLD}{Colors.WHITE}{' ' * title_padding} {menu.title.upper()} {' ' * (title_width - title_padding - len(menu.title) - 2)}{Colors.RESET}\n")
        
        # Mostrar items con mejor formato
        print(f"{Colors.CYAN}{'-' * 70}{Colors.RESET}")
        for key, item in sorted(menu.items.items()):
            formatted_item = style.menu_item(
                key=item.key,
                label=item.label,
                is_submenu=item.is_submenu,
                description=item.description,
                require_confirmation=item.require_confirmation
            )
            print(formatted_item)
        print(f"{Colors.CYAN}{'-' * 70}{Colors.RESET}\n")
        
        # Opciones de navegación mejoradas
        nav_items = []
        if menu.has_parent():
            nav_items.append(f"{Colors.BOLD}{Colors.BLUE}[0]{Colors.RESET} {Colors.CYAN}<- Volver{Colors.RESET}")
        nav_items.append(f"{Colors.BOLD}{Colors.RED}[X]{Colors.RESET} {Colors.RED}Salir{Colors.RESET}")
        nav_items.append(f"{Colors.BOLD}{Colors.MAGENTA}[?]{Colors.RESET} {Colors.MAGENTA}Ayuda{Colors.RESET}")
        
        nav_line = f"   {Colors.DIM}|{Colors.RESET} ".join(nav_items)
        print(f"   {nav_line}\n")
    
    def run(self):
        """Ejecuta el loop principal del menú"""
        while True:
            self.render()
            
            opcion = input(f"{Colors.BOLD}{Colors.MAGENTA}[*]{Colors.RESET} {Colors.CYAN}Selecciona una opcion:{Colors.RESET} ").strip().upper()
            
            if opcion == "X":
                print(f"\n{style.warning('¿Estás seguro que deseas salir?')}")
                confirm = input(f"{Colors.YELLOW}   Escribe 'S' para confirmar: {Colors.RESET}").strip().upper()
                if confirm == "S":
                    print(f"\n{style.success('¡Hasta luego! Gracias por usar el Asistente de Soporte Técnico.')}\n")
                    break
            
            elif opcion == "?":
                self._show_help()
            
            elif opcion == "0":
                if self.current_menu.has_parent():
                    self.go_back()
                else:
                    # En menú raíz, 0 puede tener otro significado
                    item = self.current_menu.get_item("0")
                    if item and item.action:
                        self.execute_action(item)
                    else:
                        print(f"\n{style.info('Ya estás en el menú principal.')}")
                        input(f"\n{Colors.CYAN}Presiona ENTER para continuar...{Colors.RESET}")
            
            else:
                item = self.current_menu.get_item(opcion)
                
                if item:
                    if item.is_submenu:
                        self.enter_submenu(item.submenu, item.label)
                    elif item.action:
                        self.execute_action(item)
                else:
                    print(f"\n{style.error('Opción inválida. Presiona [?] para ver la ayuda.')}")
                    input(f"\n{Colors.CYAN}Presiona ENTER para continuar...{Colors.RESET}")
    
    def execute_action(self, item: MenuItem):
        """
        Ejecuta la acción de un item con mejor feedback visual
        
        Args:
            item: Item cuya acción ejecutar
        """
        if item.require_confirmation:
            print(f"\n{style.warning(f'Esta operación requiere confirmación: {item.label}')}")
            confirm = input(f"{Colors.YELLOW}   ¿Deseas continuar? (S/N): {Colors.RESET}").strip().upper()
            if confirm != "S":
                print(f"\n{style.info('Operación cancelada por el usuario.')}")
                input(f"\n{Colors.CYAN}Presiona ENTER para continuar...{Colors.RESET}")
                return
        
        # Mostrar que se está ejecutando con mejor formato
        print(f"\n{Colors.CYAN}{'-' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}[*] Ejecutando:{Colors.RESET} {Colors.WHITE}{item.label}{Colors.RESET}")
        print(f"{Colors.CYAN}{'-' * 70}{Colors.RESET}\n")
        
        try:
            # Pasar contexto a la acción si la acepta
            import inspect
            sig = inspect.signature(item.action)
            
            if len(sig.parameters) == 0:
                item.action()
            elif len(sig.parameters) == 1:
                # Puede ser executor o hostname
                if 'executor' in self.context:
                    item.action(self.context['executor'])
                elif 'hostname' in self.context:
                    item.action(self.context['hostname'])
                else:
                    item.action()
            elif len(sig.parameters) >= 2:
                # Típicamente (executor, hostname)
                item.action(
                    self.context.get('executor'),
                    self.context.get('hostname', '')
                )
            
            print(f"\n{Colors.CYAN}{'-' * 70}{Colors.RESET}")
            print(f"{style.success(f'{item.label} completado exitosamente.')}")
            print(f"{Colors.CYAN}{'-' * 70}{Colors.RESET}")
            
        except KeyboardInterrupt:
            print(f"\n\n{style.warning('Operación interrumpida por el usuario.')}")
            input(f"\n{Colors.CYAN}Presiona ENTER para continuar...{Colors.RESET}")
        except Exception as e:
            print(f"\n{Colors.CYAN}{'-' * 70}{Colors.RESET}")
            print(f"{style.error(f'Error al ejecutar {item.label}: {str(e)}')}")
            print(f"{Colors.CYAN}{'-' * 70}{Colors.RESET}")
            input(f"\n{Colors.CYAN}Presiona ENTER para continuar...{Colors.RESET}")
    
    def enter_submenu(self, submenu: Menu, label: str):
        """
        Entra a un submenú
        
        Args:
            submenu: Submenú a mostrar
            label: Etiqueta del submenú para breadcrumbs
        """
        self.breadcrumbs.append(self.current_menu.title if self.current_menu != self.root_menu else "Inicio")
        self.current_menu = submenu
    
    def go_back(self):
        """Vuelve al menú padre"""
        if self.current_menu.has_parent():
            self.current_menu = self.current_menu.parent
            if self.breadcrumbs:
                self.breadcrumbs.pop()
    
    def _show_help(self):
        """Muestra ayuda contextual con mejor formato"""
        clear_screen()
        
        # Header de ayuda
        help_title = f"AYUDA - {self.current_menu.title.upper()}"
        print(f"\n{Colors.BG_MAGENTA}{Colors.BOLD}{Colors.WHITE} {help_title:68} {Colors.RESET}\n")
        
        # Navegación
        print(f"{style.title('[*] Navegacion:', Colors.CYAN)}\n")
        print(f"   {Colors.GREEN}[*]{Colors.RESET} Ingresa el {Colors.BOLD}{Colors.GREEN}numero/letra{Colors.RESET} de la opcion y presiona ENTER")
        print(f"   {Colors.BLUE}[*]{Colors.RESET} {Colors.BOLD}{Colors.BLUE}[0]{Colors.RESET} para volver al menu anterior")
        print(f"   {Colors.RED}[*]{Colors.RESET} {Colors.BOLD}{Colors.RED}[X]{Colors.RESET} para salir de la aplicacion")
        print(f"   {Colors.MAGENTA}[*]{Colors.RESET} {Colors.BOLD}{Colors.MAGENTA}[?]{Colors.RESET} para ver esta ayuda\n")
        
        # Opciones disponibles
        print(f"{style.title('[*] Opciones disponibles en este menu:', Colors.CYAN)}\n")
        for key, item in sorted(self.current_menu.items.items()):
            tipo = f"{Colors.YELLOW}Submenu{Colors.RESET}" if item.is_submenu else f"{Colors.GREEN}Accion{Colors.RESET}"
            desc = f" {Colors.DIM}* {item.description}{Colors.RESET}" if item.description else ""
            conf = f" {Colors.RED}[Requiere confirmacion]{Colors.RESET}" if item.require_confirmation else ""
            print(f"   {Colors.BOLD}{Colors.GREEN}[{item.key}]{Colors.RESET} {item.label} ({tipo}){desc}{conf}")
        
        print(f"\n{style.info('[*] Tip: Las opciones marcadas con [Requiere confirmacion] pediran tu confirmacion antes de ejecutarse.')}")
        
        # Context info
        if self.context:
            print(f"\n{style.title('[*] Contexto actual:', Colors.CYAN)}\n")
            if 'hostname' in self.context:
                print(f"   {Colors.GREEN}[*] Equipo:{Colors.RESET} {Colors.WHITE}{self.context['hostname']}{Colors.RESET}")
            if 'executor' in self.context:
                exec_type = type(self.context['executor']).__name__
                print(f"   {Colors.CYAN}[*] Ejecutor:{Colors.RESET} {Colors.WHITE}{exec_type}{Colors.RESET}")
        
        print(f"\n{Colors.CYAN}{'-' * 70}{Colors.RESET}")
        input(f"\n{Colors.CYAN}Presiona ENTER para volver al menú...{Colors.RESET}")


