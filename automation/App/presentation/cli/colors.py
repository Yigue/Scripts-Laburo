"""
Sistema de colores y estilos para la consola
Proporciona una interfaz unificada para formateo visual
"""
from colorama import Fore, Back, Style, init

# Inicializar colorama
init(autoreset=True)


class Colors:
    """Clase estática con colores y estilos predefinidos"""
    
    # Colores básicos
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT
    DIM = Style.DIM
    
    # Colores de texto
    BLACK = Fore.BLACK
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    
    # Colores de fondo
    BG_BLACK = Back.BLACK
    BG_RED = Back.RED
    BG_GREEN = Back.GREEN
    BG_YELLOW = Back.YELLOW
    BG_BLUE = Back.BLUE
    BG_MAGENTA = Back.MAGENTA
    BG_CYAN = Back.CYAN
    BG_WHITE = Back.WHITE


class ConsoleStyle:
    """Utilidades para estilizar la consola"""
    
    @staticmethod
    def header(text: str, char: str = "═", color: str = Colors.CYAN) -> str:
        """
        Crea un encabezado estilizado
        
        Args:
            text: Texto del encabezado
            char: Carácter para el borde
            color: Color a usar
            
        Returns:
            str: Encabezado formateado
        """
        width = 70
        padding = (width - len(text) - 4) // 2
        return f"{color}{char * width}{Colors.RESET}\n{color}{char}{Colors.RESET} {Colors.BOLD}{text}{Colors.RESET} {color}{char * (width - padding - len(text) - 3)}{Colors.RESET}\n{color}{char * width}{Colors.RESET}"
    
    @staticmethod
    def separator(char: str = "─", color: str = Colors.CYAN, width: int = 70) -> str:
        """
        Crea un separador
        
        Args:
            char: Carácter para el separador
            color: Color a usar
            width: Ancho del separador
            
        Returns:
            str: Separador formateado
        """
        return f"{color}{char * width}{Colors.RESET}"
    
    @staticmethod
    def box(text: str, color: str = Colors.CYAN, width: int = 70) -> str:
        """
        Envuelve texto en una caja
        
        Args:
            text: Texto a mostrar
            color: Color del borde
            width: Ancho de la caja
            
        Returns:
            str: Texto en caja
        """
        lines = text.split('\n')
        result = f"{color}+{'=' * (width - 2)}+{Colors.RESET}\n"
        for line in lines:
            padding = width - len(line) - 4
            result += f"{color}|{Colors.RESET} {line}{' ' * padding} {color}|{Colors.RESET}\n"
        result += f"{color}+{'=' * (width - 2)}+{Colors.RESET}"
        return result
    
    @staticmethod
    def success(text: str) -> str:
        """Formatea un mensaje de éxito"""
        return f"{Colors.GREEN}[OK]{Colors.RESET} {Colors.GREEN}{text}{Colors.RESET}"
    
    @staticmethod
    def error(text: str) -> str:
        """Formatea un mensaje de error"""
        return f"{Colors.RED}[X]{Colors.RESET} {Colors.RED}{text}{Colors.RESET}"
    
    @staticmethod
    def warning(text: str) -> str:
        """Formatea un mensaje de advertencia"""
        return f"{Colors.YELLOW}[!]{Colors.RESET} {Colors.YELLOW}{text}{Colors.RESET}"
    
    @staticmethod
    def info(text: str) -> str:
        """Formatea un mensaje informativo"""
        return f"{Colors.CYAN}[i]{Colors.RESET} {Colors.CYAN}{text}{Colors.RESET}"
    
    @staticmethod
    def menu_item(key: str, label: str, is_submenu: bool = False, description: str = "", 
                  require_confirmation: bool = False) -> str:
        """
        Formatea un item de menú
        
        Args:
            key: Tecla de acceso
            label: Etiqueta del item
            is_submenu: Si es un submenú
            description: Descripción adicional
            require_confirmation: Si requiere confirmación
            
        Returns:
            str: Item formateado
        """
        if is_submenu:
            icon = f"{Colors.YELLOW}>>{Colors.RESET}"
            key_color = Colors.YELLOW
        else:
            icon = f"{Colors.GREEN}[*]{Colors.RESET}"
            key_color = Colors.GREEN
        
        result = f"   {icon} {Colors.BOLD}{key_color}[{key}]{Colors.RESET} {Colors.WHITE}{label}{Colors.RESET}"
        
        if description:
            result += f" {Colors.DIM}{Colors.WHITE}• {description}{Colors.RESET}"
        
        if require_confirmation:
            result += f" {Colors.RED}[Requiere confirmación]{Colors.RESET}"
        
        return result
    
    @staticmethod
    def title(text: str, color: str = Colors.CYAN) -> str:
        """Formatea un título"""
        return f"{Colors.BOLD}{color}{text}{Colors.RESET}"
    
    @staticmethod
    def highlight(text: str, color: str = Colors.YELLOW) -> str:
        """Resalta texto"""
        return f"{Colors.BOLD}{color}{text}{Colors.RESET}"


# Instancia global para uso fácil
style = ConsoleStyle()

