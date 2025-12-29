"""
Menú Principal de Automatización
Integra todas las herramientas de automatización disponibles
"""
import sys
import os
import subprocess

# Agregar directorios al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.common import clear_screen, clear_cached_credentials


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


def mostrar_menu_utilidades():
    """Muestra el submenú de utilidades"""
    base_path = os.path.join(os.path.dirname(__file__), "utils")
    
    while True:
        clear_screen()
        print("=" * 60)
        print("🛠️  UTILIDADES")
        print("=" * 60)
        print("\n1. Consola remota (PsExec/WinRM)")
        print("2. Test WinRM Helper")
        print("3. Test Ansible Helper")
        print("\n0. ← Volver al menú principal")
        
        opcion = input("\nOpción: ").strip()
        
        if opcion == "1":
            ejecutar_script(os.path.join(base_path, "comand", "EjecutarConsola.py"))
        elif opcion == "2":
            ejecutar_script(os.path.join(base_path, "WinRM_Helper.py"))
        elif opcion == "3":
            ejecutar_script(os.path.join(base_path, "Ansible_Helper.py"))
        elif opcion == "0":
            break
        else:
            print("❌ Opción inválida")
            input("\nPresioná ENTER para continuar...")


def mostrar_info():
    """Muestra información sobre las herramientas disponibles"""
    clear_screen()
    print("=" * 60)
    print("ℹ️  INFORMACIÓN")
    print("=" * 60)
    
    print("""
📡 HERRAMIENTAS WI-FI
    - Analizador: Recolecta información de conexión Wi-Fi
    - Forzar 5GHz: Intenta conectar a banda 5GHz
    - Reportes: Genera reportes CSV y clasificación

📦 GESTIÓN DE SOFTWARE
    - Buscar: Busca software por nombre/publisher
    - Listar: Lista todo el software con filtros
    - Eliminar: Desinstala software
    - Dell Command: Elimina Dell Command | Update

🔧 REMEDIACIÓN
    - OneDrive: Repara problemas de sincronización
    - Outlook: Repara perfiles y OST
    - SCCM: Repara cliente SCCM
    - VPN: Repara conexiones VPN

🛠️  UTILIDADES
    - Consola remota: Ejecuta comandos en equipos remotos
    - WinRM Helper: Gestión de conexiones WinRM
    - Ansible Helper: Integración con Ansible

📋 REQUISITOS
    - Python 3.7+
    - PsExec (opcional, para conexiones remotas)
    - Ansible + pywinrm (opcional, para playbooks)
    """)
    
    input("\nPresioná ENTER para volver...")


def main():
    """Función principal"""
    while True:
        clear_screen()
        print("=" * 60)
        print("🚀 MENÚ PRINCIPAL DE AUTOMATIZACIÓN")
        print("=" * 60)
        print("""
    1. 📡 Herramientas Wi-Fi
    2. 📦 Gestión de Software
    3. 🔧 Herramientas de Remediación
    4. 🛠️  Utilidades
    
    5. ℹ️  Información
    6. 🔐 Limpiar credenciales en caché
    
    0. 🚪 Salir
        """)
        
        opcion = input("Opción: ").strip()
        
        if opcion == "1":
            mostrar_menu_wifi()
        elif opcion == "2":
            mostrar_menu_software()
        elif opcion == "3":
            mostrar_menu_remediacion()
        elif opcion == "4":
            mostrar_menu_utilidades()
        elif opcion == "5":
            mostrar_info()
        elif opcion == "6":
            clear_cached_credentials()
            input("\nPresioná ENTER para continuar...")
        elif opcion == "0":
            clear_screen()
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")
            input("\nPresioná ENTER para continuar...")


if __name__ == "__main__":
    main()

