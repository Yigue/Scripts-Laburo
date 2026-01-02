"""
Menú Principal de Automatización - Asistente de Soporte Técnico
Integra todas las herramientas de automatización disponibles
Usa WinRM para conexiones remotas (sesión de administrador actual)
"""
import sys
import os
import subprocess
from functools import partial

# Agregar directorios al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.common import clear_screen
from utils.remote_executor import RemoteExecutor

# Importar módulos remotos reorganizados por categoría
from remote.hardware import (
    system_info,
    configurar_equipo,
    optimizar,
    reiniciar,
    dell_command,
    activar_windows,
)
from remote.redes import wcorp_fix
from remote.software import office_install, aplicaciones
from remote.impresoras import impresoras as impresoras_mod, zebra_calibrar
from remote import consola_remota


def ejecutar_script(script_path):
    """Ejecuta un script Python"""
    if not os.path.exists(script_path):
        print(f"❌ Script no encontrado: {script_path}")
        input("\nPresioná ENTER para continuar...")
        return
    
    try:
        subprocess.run([sys.executable, script_path], check=False)
    except KeyboardInterrupt:
        print("\n⚠️  Script interrumpido")
    except Exception as e:
        print(f"❌ Error ejecutando script: {e}")
        input("\nPresioná ENTER para continuar...")


def mostrar_banner():
    """Muestra el banner del asistente"""
    print("""
          ░██████╗░█████╗░██████╗░░█████╗░██████╗░████████╗███████╗
          ██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔════╝
          ╚█████╗░██║░░██║██████╔╝██║░░██║██████╔╝░░░██║░░░█████╗░░
          ░╚═══██╗██║░░██║██╔═══╝░██║░░██║██╔══██╗░░░██║░░░██╔══╝░░
          ██████╔╝╚█████╔╝██║░░░░░╚█████╔╝██║░░██║░░░██║░░░███████╗
          ╚═════╝░░╚════╝░╚═╝░░░░░░╚════╝░╚═╝░░╚═╝░░░╚═╝░░░╚══════╝

                   Bienvenido al Asistente de Soporte Técnico
                          (Versión Python con WinRM)
    """)


def mostrar_menu_principal(hostname: str):
    """Muestra el menú principal con solo categorías"""
    print(f"""
   Equipo Remoto: {hostname}
   ════════════════════════════════════════════════════════════

   H. Hardware y Config
   R. Redes y Wi-Fi
   I. Impresoras
   S. Gestión de Software
   C. Consola remota
   W. Herramientas WiFi
   
   ════════════════════════════════════════════════════════════
   
   0. Cambiar equipo                   X. Salir
    """)


def mostrar_menu_wifi():
    """Muestra el submenú de herramientas Wi-Fi"""
    base_path = os.path.join(os.path.dirname(__file__), "wifi")
    
    while True:
        clear_screen()
        print("=" * 60)
        print("📡 HERRAMIENTAS WI-FI")
        print("=" * 60)
        print("\n1. Analizador de Wi-Fi (local/remoto)")
        print("2. Forzar conexión a 5GHz")
        print("3. Generar reportes Wi-Fi")
        print("\n0. ← Volver al menú principal")
        
        opcion = input("\nOpción: ").strip()
        
        if opcion == "1":
            ejecutar_script(os.path.join(base_path, "wifi_analyzer.py"))
        elif opcion == "2":
            ejecutar_script(os.path.join(base_path, "wifi_force_5ghz.py"))
        elif opcion == "3":
            ejecutar_script(os.path.join(base_path, "wifi_report.py"))
        elif opcion == "0":
            break
        else:
            print("❌ Opción inválida")
            input("\nPresioná ENTER para continuar...")


def mostrar_menu_software():
    """Muestra el submenú de gestión de software"""
    base_path = os.path.join(os.path.dirname(__file__), "utils", "sofware")
    
    while True:
        clear_screen()
        print("=" * 60)
        print("📦 GESTIÓN DE SOFTWARE")
        print("=" * 60)
        print("\n1. Buscar software instalado")
        print("2. Listar software (interactivo)")
        print("3. Eliminar software")
        print("4. Eliminar Dell Command | Update")
        print("\n0. ← Volver al menú principal")
        
        opcion = input("\nOpción: ").strip()
        
        if opcion == "1":
            ejecutar_script(os.path.join(base_path, "BuscarSoftware.py"))
        elif opcion == "2":
            ejecutar_script(os.path.join(base_path, "ListarSoftware.py"))
        elif opcion == "3":
            ejecutar_script(os.path.join(base_path, "DeleteSofware.py"))
        elif opcion == "4":
            ejecutar_script(os.path.join(base_path, "BorrarDellComand.py"))
        elif opcion == "0":
            break
        else:
            print("❌ Opción inválida")
            input("\nPresioná ENTER para continuar...")


def mostrar_menu_categoria(titulo: str, opciones: dict):
    """Muestra un submenú de categoría"""
    nombres = {
        "1": "Mostrar especificaciones",
        "2": "Terminar de configurar",
        "3": "Optimizar",
        "4": "Reiniciar",
        "5": "Actualizar drivers DELL",
        "6": "WCORP (Script, cleanDNS, GPUPDATE)",
        "7": "Activar Windows",
        "9": "Instalar Impresora",
        "10": "Calibrar Zebra WiFi",
        "W": "Herramientas WiFi",
    }
    
    while True:
        clear_screen()
        print("=" * 60)
        print(f"📋 {titulo.upper()}")
        print("=" * 60)
        print()
        for key in sorted(opciones.keys(), key=lambda x: (x.isdigit(), int(x) if x.isdigit() else 0)):
            nombre = nombres.get(key, f"Opción {key}")
            print(f"{key}. {nombre}")
        print("\n0. ← Volver al menú principal")
        
        opcion = input("\nOpción: ").strip().upper()
        
        if opcion == "0":
            break
        
        handler = opciones.get(opcion)
        if handler:
            clear_screen()
            try:
                handler()
            except Exception as e:
                print(f"❌ Error ejecutando opción: {e}")
                input("\nPresioná ENTER para continuar...")
        else:
            print("❌ Opción inválida")
            input("\nPresioná ENTER para continuar...")


def mostrar_menu_remediacion():
    """Muestra el submenú de herramientas de remediación"""
    base_path = os.path.join(os.path.dirname(__file__), "remediation")
    
    while True:
        clear_screen()
        print("=" * 60)
        print("🔧 HERRAMIENTAS DE REMEDIACIÓN")
        print("=" * 60)
        print("\n1. Reparar OneDrive")
        print("2. Reparar Outlook")
        print("3. Reparar Cliente SCCM")
        print("4. Reparar VPN")
        print("\n0. ← Volver al menú principal")
        
        opcion = input("\nOpción: ").strip()
        
        if opcion == "1":
            ejecutar_script(os.path.join(base_path, "onedrive_fix.py"))
        elif opcion == "2":
            ejecutar_script(os.path.join(base_path, "outlook_fix.py"))
        elif opcion == "3":
            ejecutar_script(os.path.join(base_path, "sccm_fix.py"))
        elif opcion == "4":
            ejecutar_script(os.path.join(base_path, "vpn_fix.py"))
        elif opcion == "0":
            break
        else:
            print("❌ Opción inválida")
            input("\nPresioná ENTER para continuar...")


def conectar_equipo(executor: RemoteExecutor):
    """
    Solicita y verifica conexión a un equipo remoto
    
    Returns:
        str: Nombre del equipo o None si falla
    """
    while True:
        hostname = input("\nInventario: ").strip()
        if not hostname:
            print("❌ Debe ingresar un inventario")
            continue
        
        print()
        conn = executor.test_connection(hostname, verbose=True)
        
        if conn["ready"]:
            method = conn.get("preferred_method", "desconocido")
            print(f"\n✅ Conexión exitosa con {hostname} (método: {method.upper()})")
            
            # Crear carpeta TEMP si no existe
            executor.run_command(hostname, 
                'if (!(Test-Path "C:\\TEMP")) { New-Item -Path "C:\\TEMP" -ItemType Directory -Force }',
                verbose=False
            )
            
            return hostname
        else:
            print(f"\n❌ No se pudo conectar con {hostname}")
            for error in conn.get("errors", []):
                print(f"   • {error}")
            
            reintentar = input("\n¿Intentar con otro equipo? (S/N): ").strip().upper()
            if reintentar != "S":
                return None


def main():
    """Función principal - Menú principal del asistente"""
    executor = RemoteExecutor()
    hostname = None
    
    while True:
        clear_screen()
        mostrar_banner()
        
        # Si no hay equipo conectado, solicitar uno
        if not hostname:
            hostname = conectar_equipo(executor)
            if not hostname:
                print("\n👋 ¡Hasta luego!")
                break
            continue
        
        # Mostrar menú principal (solo categorías)
        clear_screen()
        mostrar_banner()
        mostrar_menu_principal(hostname)
        
        opcion = input("   Opción: ").strip().upper()
        
        # Handlers de categorías (sin opciones numéricas en el principal)
        handlers = {
            "H": lambda: mostrar_menu_categoria("Hardware y Config", {
                "1": partial(system_info.ejecutar, executor, hostname),
                "2": partial(configurar_equipo.ejecutar, executor, hostname),
                "3": partial(optimizar.ejecutar, executor, hostname),
                "4": partial(reiniciar.ejecutar, executor, hostname),
                "5": partial(dell_command.ejecutar, executor, hostname),
                "7": partial(activar_windows.ejecutar, executor, hostname),
            }),
            "R": lambda: mostrar_menu_categoria("Redes y Wi-Fi", {
                "6": partial(wcorp_fix.ejecutar, executor, hostname),
                "W": mostrar_menu_wifi,
            }),
            "I": lambda: mostrar_menu_categoria("Impresoras", {
                "9": partial(impresoras_mod.ejecutar, executor, hostname),
                "10": partial(zebra_calibrar.ejecutar, executor, hostname),
            }),
            "S": mostrar_menu_software,
            "C": partial(consola_remota.ejecutar, executor, hostname),
            "W": mostrar_menu_wifi,
        }

        if opcion == "0":
            print("\n🔄 Cambiando equipo...")
            hostname = conectar_equipo(executor)
            if not hostname:
                print("\n👋 ¡Hasta luego!")
                break
            continue

        if opcion == "X":
            clear_screen()
            print("👋 ¡Hasta luego!")
            break

        handler = handlers.get(opcion)
        if handler:
            clear_screen()
            try:
                handler()
            except Exception as e:
                print(f"\n❌ Error ejecutando opción: {e}")
                import traceback
                traceback.print_exc()
                input("\nPresioná ENTER para continuar...")
        else:
            print("❌ Opción inválida")
            input("\nPresioná ENTER para continuar...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print("\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        input("\nPresioná ENTER para salir...")
