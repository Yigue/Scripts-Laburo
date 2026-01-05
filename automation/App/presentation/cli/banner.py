"""
Banner - Muestra banners ASCII art estilo retro
Compatible con Windows con diseño tipo terminal clásica
"""
from colorama import Fore, Back, Style
from .colors import Colors, ConsoleStyle

style = ConsoleStyle()


def show_banner():
    """Muestra el banner principal con ASCII art estilo bloques"""
    # ASCII art estilo bloques para "SOPORTE"
    banner = f"""
{Colors.BOLD}{Colors.RED} .d8888b.   .d88888b.  8888888b.   .d88888b.  8888888b.  88888888888 8888888888 {Colors.RESET}
{Colors.BOLD}{Colors.RED}d88P  Y88b d88P" "Y88b 888   Y88b d88P" "Y88b 888   Y88b     888     888        {Colors.RESET}
{Colors.BOLD}{Colors.RED}Y88b.      888     888 888    888 888     888 888    888     888     888        {Colors.RESET}
{Colors.BOLD}{Colors.RED} "Y888b.   888     888 888   d88P 888     888 888   d88P     888     8888888    {Colors.RESET}
{Colors.BOLD}{Colors.RED}    "Y88b. 888     888 8888888P"  888     888 8888888P"      888     888        {Colors.RESET}
{Colors.BOLD}{Colors.RED}      "888 888     888 888        888     888 888 T88b       888     888        {Colors.RESET}
{Colors.BOLD}{Colors.RED}Y88b  d88P Y88b. .d88P 888        Y88b. .d88P 888  T88b      888     888        {Colors.RESET}
{Colors.BOLD}{Colors.RED} "Y8888P"   "Y88888P"  888         "Y88888P"  888   T88b     888     8888888888 {Colors.RESET}

{Colors.WHITE}                    Bienvenido al Asistente de Soporte Tecnico{Colors.RESET}
"""
    print(banner)


def show_welcome_message(hostname: str):
    """
    Muestra mensaje con información del equipo estilo clásico
    
    Args:
        hostname: Nombre del equipo remoto
    """
    print(f"{Colors.WHITE}            Por favor, a continuacion seleccione la opcion a ejecutar:{Colors.RESET}")
    print()
    print(f"{Colors.WHITE}                Equipo Remoto . . . . . : {Colors.YELLOW}{hostname}{Colors.RESET}")
    print()
    print(f"{Colors.CYAN}{'=' * 80}{Colors.RESET}")

