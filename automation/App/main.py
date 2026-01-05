"""
Asistente de Soporte Técnico - Entry Point Principal
Menú plano con opciones en columnas estilo clásico
"""
import sys
import os
from functools import partial

# Agregar directorio al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from presentation.cli import show_banner, show_welcome_message
from presentation.cli.colors import Colors, ConsoleStyle
from presentation.cli.flat_menu import FlatMenu, FlatMenuRenderer
from utils.remote_executor import RemoteExecutor
from utils.common import clear_screen
from shared.validators import validate_hostname

style = ConsoleStyle()

# Importar módulos de features
from features.hardware import (
    system_info,
    configurar_equipo,
    optimizar,
    reiniciar,
    dell_command,
    activar_windows,
)
from features.diagnostic import wcorp_fix
from features.software import office_install, aplicaciones
from features.printers import impresoras as impresoras_mod, zebra_calibrar
from features import consola_remota


def solicitar_hostname() -> str:
    """
    Solicita el hostname al usuario con validación
    
    Returns:
        str: Hostname válido
    """
    while True:
        clear_screen()
        show_banner()
        
        print(f"{Colors.WHITE}            Ingrese el nombre del equipo remoto:{Colors.RESET}")
        print()
        
        hostname = input(f"                Equipo . . . . . : ").strip().upper()
        
        if not hostname:
            print(f"\n{style.error('El hostname no puede estar vacio.')}")
            input(f"\n{Colors.CYAN}Presiona ENTER para continuar...{Colors.RESET}")
            continue
        
        # Validar formato (opcional - solo warning)
        try:
            validate_hostname(hostname, raise_on_invalid=True)
            return hostname
        except Exception as e:
            print(f"\n{style.warning(f'Advertencia: {e}')}")
            confirmar = input(f"{Colors.YELLOW}Continuar de todas formas? (S/N): {Colors.RESET}").strip().upper()
            if confirmar == "S":
                return hostname


def crear_menu_principal(executor, hostname: str) -> FlatMenu:
    """
    Crea el menú principal con categorías y opciones
    
    Args:
        executor: Ejecutor remoto
        hostname: Hostname del equipo remoto
        
    Returns:
        FlatMenu (CategoryMenu): Menú configurado
    """
    menu = FlatMenu("Menu Principal")
    
    # ═══════════════════════════════════════════════════════════════
    # [H] HARDWARE Y SISTEMA
    # ═══════════════════════════════════════════════════════════════
    menu.add_category("H", "HARDWARE Y SISTEMA")
    menu.add_item("H", "Mostrar especificaciones", 
                  partial(system_info.ejecutar, executor, hostname))
    menu.add_item("H", "Terminar de configurar", 
                  partial(configurar_equipo.ejecutar, executor, hostname))
    menu.add_item("H", "Optimizar sistema", 
                  partial(optimizar.ejecutar, executor, hostname))
    menu.add_item("H", "Reiniciar equipo", 
                  partial(reiniciar.ejecutar, executor, hostname))
    menu.add_item("H", "Actualizar drivers DELL", 
                  partial(dell_command.ejecutar, executor, hostname))
    menu.add_item("H", "Activar Windows", 
                  partial(activar_windows.ejecutar, executor, hostname))
    
    # ═══════════════════════════════════════════════════════════════
    # [R] REDES Y CONECTIVIDAD
    # ═══════════════════════════════════════════════════════════════
    menu.add_category("R", "REDES Y CONECTIVIDAD")
    menu.add_item("R", "WCORP (Script, cleanDNS, GPUPDATE)", 
                  partial(wcorp_fix.ejecutar, executor, hostname))
    
    # ═══════════════════════════════════════════════════════════════
    # [S] SOFTWARE
    # ═══════════════════════════════════════════════════════════════
    menu.add_category("S", "SOFTWARE")
    menu.add_item("S", "Instalar Office 365", 
                  partial(office_install.ejecutar, executor, hostname))
    menu.add_item("S", "Gestionar aplicaciones", 
                  partial(aplicaciones.ejecutar, executor, hostname))
    
    # ═══════════════════════════════════════════════════════════════
    # [I] IMPRESORAS
    # ═══════════════════════════════════════════════════════════════
    menu.add_category("I", "IMPRESORAS")
    menu.add_item("I", "Gestionar impresoras", 
                  partial(impresoras_mod.ejecutar, executor, hostname))
    menu.add_item("I", "Calibrar Zebra", 
                  partial(zebra_calibrar.ejecutar, executor, hostname))
    
    # ═══════════════════════════════════════════════════════════════
    # [C] CONSOLA REMOTA
    # ═══════════════════════════════════════════════════════════════
    menu.add_category("C", "CONSOLA REMOTA")
    menu.add_item("C", "Abrir consola remota", 
                  partial(consola_remota.ejecutar, executor, hostname))
    
    return menu


def main():
    """Función principal de la aplicación"""
    try:
        while True:
            # Solicitar hostname
            hostname = solicitar_hostname()
            
            # Crear executor
            executor = RemoteExecutor()
            
            # Crear menú plano
            menu = crear_menu_principal(executor, hostname)
            
            # Crear renderer
            renderer = FlatMenuRenderer(
                menu=menu,
                hostname=hostname,
                executor=executor,
                show_banner_func=show_banner,
                show_welcome_func=show_welcome_message
            )
            
            # Ejecutar menú
            result = renderer.run()
            
            if result == "exit":
                break
            # Si result es "change_host", el loop continúa
            
    except KeyboardInterrupt:
        print(f"\n\n{style.warning('Programa interrumpido por el usuario.')}")
    except Exception as e:
        print(f"\n{style.error(f'Error inesperado: {e}')}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n{style.success('Gracias por usar el Asistente de Soporte Tecnico!')}")
        print(f"{Colors.DIM}{Colors.WHITE}Hasta luego...{Colors.RESET}\n")


if __name__ == "__main__":
    main()

