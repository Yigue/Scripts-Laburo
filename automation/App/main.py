"""
Asistente de Soporte Técnico - Entry Point Principal
Menú plano con opciones en columnas estilo clásico
"""
import sys
import os
import argparse
import re
from functools import partial
from typing import List

# Agregar directorio al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from presentation.cli import show_banner, show_welcome_message
from presentation.cli.colors import Colors, ConsoleStyle
from presentation.cli.flat_menu import FlatMenu, FlatMenuRenderer
from utils.remote_executor import RemoteExecutor
from utils.common import clear_screen
from utils.process_launcher import launch_menu_for_host
from utils.status_provider import get_initial_status
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
from features.remedations import (
    sccm_fix,
    onedrive_fix,
    outlook_fix,
    vpn_fix,
    disk_management
)
from features.wifi import wifi_analyzer
from features import consola_remota


def solicitar_hostnames() -> List[str]:
    """
    Solicita uno o más hostnames al usuario
    Permite ingresar múltiples separados por coma, espacio o punto y coma
    
    Returns:
        List[str]: Lista de hostnames válidos
    """
    while True:
        clear_screen()
        show_banner()
        
        print(f"{Colors.WHITE}            Ingrese el/los nombre(s) del equipo(s) remoto(s):{Colors.RESET}")
        print(f"{Colors.DIM}            (Separar múltiples con coma, espacio o punto y coma){Colors.RESET}")
        print()
        
        entrada = input(f"                Equipo(s) . . . : ").strip().upper()
        
        if not entrada:
            print(f"\n{style.error('Debe ingresar al menos un hostname.')}")
            input(f"\n{Colors.CYAN}Presiona ENTER para continuar...{Colors.RESET}")
            continue
        
        # Separar por coma, espacio o punto y coma
        hostnames = re.split(r'[,;\s]+', entrada)
        hostnames = [h.strip() for h in hostnames if h.strip()]
        
        if not hostnames:
            print(f"\n{style.error('Debe ingresar al menos un hostname.')}")
            input(f"\n{Colors.CYAN}Presiona ENTER para continuar...{Colors.RESET}")
            continue
        
        # Validar cada hostname (solo warning)
        valid_hostnames = []
        for hostname in hostnames:
            try:
                validate_hostname(hostname, raise_on_invalid=True)
                valid_hostnames.append(hostname)
            except Exception as e:
                print(f"\n{style.warning(f'Advertencia para {hostname}: {e}')}")
                confirmar = input(f"{Colors.YELLOW}Incluir {hostname} de todas formas? (S/N): {Colors.RESET}").strip().upper()
                if confirmar == "S":
                    valid_hostnames.append(hostname)
        
        if valid_hostnames:
            return valid_hostnames
        else:
            print(f"\n{style.error('No se ingresaron hostnames válidos.')}")
            input(f"\n{Colors.CYAN}Presiona ENTER para continuar...{Colors.RESET}")


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
                  partial(system_info.ejecutar, executor, hostname),
                  module_path="features.hardware.system_info")
    menu.add_item("H", "Terminar de configurar", 
                  partial(configurar_equipo.ejecutar, executor, hostname),
                  module_path="features.hardware.configurar_equipo")
    menu.add_item("H", "Optimizar sistema", 
                  partial(optimizar.ejecutar, executor, hostname),
                  module_path="features.hardware.optimizar")
    menu.add_item("H", "Reiniciar equipo", 
                  partial(reiniciar.ejecutar, executor, hostname),
                  module_path="features.hardware.reiniciar")
    menu.add_item("H", "Actualizar drivers DELL", 
                  partial(dell_command.ejecutar, executor, hostname),
                  module_path="features.hardware.dell_command")
    menu.add_item("H", "Activar Windows", 
                  partial(activar_windows.ejecutar, executor, hostname),
                  module_path="features.hardware.activar_windows")
    
    # ═══════════════════════════════════════════════════════════════
    # [R] REDES Y CONECTIVIDAD
    # ═══════════════════════════════════════════════════════════════
    menu.add_category("R", "REDES Y CONECTIVIDAD")
    menu.add_item("R", "WCORP (Script, cleanDNS, GPUPDATE)", 
                  partial(wcorp_fix.ejecutar, executor, hostname),
                  module_path="features.diagnostic.wcorp_fix")
    menu.add_item("R", "Analizar Wi-Fi",
                  partial(wifi_analyzer.ejecutar, executor, hostname),
                  module_path="features.wifi.wifi_analyzer")
    
    # ═══════════════════════════════════════════════════════════════
    # [M] MANTENIMIENTO Y REPARACION
    # ═══════════════════════════════════════════════════════════════
    menu.add_category("M", "MANTENIMIENTO Y REPARACION")
    menu.add_item("M", "Reparar Cliente SCCM",
                  partial(sccm_fix.ejecutar, executor, hostname),
                  module_path="features.remedations.sccm_fix")
    menu.add_item("M", "Reparar OneDrive",
                  partial(onedrive_fix.ejecutar, executor, hostname),
                  module_path="features.remedations.onedrive_fix")
    menu.add_item("M", "Reparar Outlook",
                  partial(outlook_fix.ejecutar, executor, hostname),
                  module_path="features.remedations.outlook_fix")
    menu.add_item("M", "Reparar VPN (FortiClient)",
                  partial(vpn_fix.ejecutar, executor, hostname),
                  module_path="features.remedations.vpn_fix")
    menu.add_item("M", "Gestión de Discos (Limpieza)",
                  partial(disk_management.ejecutar, executor, hostname),
                  module_path="features.remedations.disk_management")

    # ═══════════════════════════════════════════════════════════════
    # [S] SOFTWARE
    # ═══════════════════════════════════════════════════════════════
    menu.add_category("S", "SOFTWARE")
    menu.add_item("S", "Instalar Office 365", 
                  partial(office_install.ejecutar, executor, hostname),
                  module_path="features.software.office_install")
    menu.add_item("S", "Gestionar aplicaciones", 
                  partial(aplicaciones.ejecutar, executor, hostname),
                  module_path="features.software.aplicaciones")
    
    # ═══════════════════════════════════════════════════════════════
    # [I] IMPRESORAS
    # ═══════════════════════════════════════════════════════════════
    menu.add_category("I", "IMPRESORAS")
    menu.add_item("I", "Gestionar impresoras", 
                  partial(impresoras_mod.ejecutar, executor, hostname),
                  module_path="features.printers.impresoras")
    menu.add_item("I", "Calibrar Zebra", 
                  partial(zebra_calibrar.ejecutar, executor, hostname),
                  module_path="features.printers.zebra_calibrar")
    
    # ═══════════════════════════════════════════════════════════════
    # [C] CONSOLA REMOTA
    # ═══════════════════════════════════════════════════════════════
    menu.add_category("C", "CONSOLA REMOTA")
    menu.add_item("C", "Abrir consola remota", 
                  partial(consola_remota.ejecutar, executor, hostname),
                  module_path="features.consola_remota")
    
    return menu


def run_menu_for_host(hostname: str):
    """Ejecuta el menú para un hostname específico"""
    executor = RemoteExecutor()
    
    # 1. Probar conexión y mostrar diagnóstico
    conn = executor.test_connection(hostname)
    
    if conn["ready"]:
        # 2. Mostrar resumen de estado inicial
        print(f"\n{Colors.CYAN}       📊 Resumen de Estado:{Colors.RESET}")
        status = get_initial_status(executor, hostname)
        print(f"{Colors.WHITE}          👤 Usuario: {Colors.YELLOW}{status.get('user', 'Desconocido')}")
        print(f"{Colors.WHITE}          ⏱️  Uptime:  {Colors.YELLOW}{status.get('uptime', 'Desconocido')}")
        print(f"{Colors.WHITE}          💾 Disco C: {Colors.YELLOW}{status.get('disk', 'Desconocido')}{Colors.RESET}")
        print("-" * 60)
        
        # 3. Lanzar menú
        menu = crear_menu_principal(executor, hostname)
        renderer = FlatMenuRenderer(
            menu=menu,
            hostname=hostname,
            executor=executor,
            show_banner_func=show_banner,
            show_welcome_func=show_welcome_message
        )
        result = renderer.run()
        
        # 4. Limpiar al salir
        executor.close_sessions()
        return result
    else:
        print(f"\n{style.error(f'No se pudo conectar a {hostname}')}")
        for diag in conn.get("diagnostics", []):
            print(f"      {diag}")
        input(f"\n{Colors.CYAN}Presiona ENTER para volver...{Colors.RESET}")
        return None


def parse_args():
    """Parsea argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Asistente de Soporte Técnico'
    )
    parser.add_argument(
        '--hostname', '-H',
        help='Hostname del equipo (usado para lanzamiento desde process_launcher)'
    )
    return parser.parse_args()


def main():
    """Función principal de la aplicación"""
    args = parse_args()
    
    try:
        # Si se pasó hostname por argumento, ir directo al menú
        if args.hostname:
            result = run_menu_for_host(args.hostname.upper())
            if result == "exit":
                return
        
        while True:
            # Solicitar hostnames (puede ser múltiple)
            hostnames = solicitar_hostnames()
            
            if len(hostnames) == 1:
                # Un solo equipo: mostrar menú en esta consola
                result = run_menu_for_host(hostnames[0])
                
                if result == "exit":
                    break
                # Si result es "change_host", el loop continúa
            else:
                # Múltiples equipos: Preguntar modo
                print(f"\n{Colors.CYAN}    Seleccionaste {len(hostnames)} equipos.{Colors.RESET}")
                print(f"    [1] Abrir menús individuales (Ventana separada por equipo)")
                print(f"    [2] Ejecutar una operación en TODOS (Masivo)")
                
                modo = input(f"\n    Opción [1/2]: ").strip()
                
                if modo == "2":
                    # Operación Masiva
                    menu_temp = crear_menu_principal(None, "MASIVO")
                    print(f"\n{Colors.CYAN}    --- SELECCIONE OPERACIÓN MASIVA ---{Colors.RESET}")
                    
                    # Mostrar opciones simplificadas
                    items_masivos = []
                    idx = 1
                    for cat_id in menu_temp.categories:
                        cat = menu_temp.categories[cat_id]
                        print(f"\n      [{cat.label}]")
                        for item in cat.items:
                            print(f"        {idx}. {item.label}")
                            items_masivos.append(item)
                            idx += 1
                    
                    try:
                        sel = input(f"\n    Seleccione número (0 para cancelar): ").strip()
                        if sel.isdigit() and 0 < int(sel) <= len(items_masivos):
                            item_sel = items_masivos[int(sel)-1]
                            print(f"\n{Colors.YELLOW}    🚀 Lanzando '{item_sel.label}' en {len(hostnames)} equipos...{Colors.RESET}")
                            
                            from utils.gui_launcher import launch_operation_in_gui
                            for hostname in hostnames:
                                launch_operation_in_gui(
                                    module_path=item_sel.module_path,
                                    hostname=hostname,
                                    label=item_sel.label
                                )
                            print(f"\n{style.success('Operaciones masivas iniciadas en ventanas separadas.')}")
                        else:
                            print(f"\n{style.warning('Operación cancelada.')}")
                    except Exception as e:
                        print(f"\n{style.error(f'Error en selección masiva: {e}')}")
                else:
                    # Múltiples equipos: abrir cada uno en nueva ventana
                    print(f"\n{Colors.CYAN}Abriendo ventanas para {len(hostnames)} equipo(s)...{Colors.RESET}")
                    for hostname in hostnames:
                        print(f"  {Colors.WHITE}-> Lanzando menú para {Colors.YELLOW}{hostname}{Colors.RESET}")
                        launch_menu_for_host(hostname)
                    
                    print(f"\n{style.success('Todas las ventanas fueron lanzadas.')}")
                
                # Preguntar si continuar o salir
                opcion = input(f"\n{Colors.CYAN}Ingresar más equipos? (S/N): {Colors.RESET}").strip().upper()
                if opcion != "S":
                    break
            
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
