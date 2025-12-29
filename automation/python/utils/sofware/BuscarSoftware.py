"""
Script para buscar software instalado en Windows
Permite buscar por nombre y publisher, funciona local o remotamente
"""
import sys
import os
import subprocess
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.psexec_helper import PsExecHelper
from utils.common import clear_screen, load_config, get_credentials


def buscar_software_local(nombre, publisher=""):
    """
    Busca software instalado en el equipo local usando PowerShell
    
    Args:
        nombre: Nombre del software a buscar (búsqueda parcial)
        publisher: Publisher del software (opcional)
    
    Returns:
        list: Lista de software encontrado, cada elemento es un dict con:
              DisplayName, DisplayVersion, Publisher, UninstallString, PSChildName
    """
    # Construir comando PowerShell
    ps_command = f"""
    $searchName = "{nombre}"
    $searchPublisher = "{publisher}"
    
    $apps = Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | 
      Where-Object {{ 
        ($_.DisplayName -like "*$searchName*") -and
        (($searchPublisher -eq "") -or ($_.Publisher -like "*$searchPublisher*"))
      }} | 
      Select-Object DisplayName, DisplayVersion, Publisher, UninstallString, PSChildName, InstallDate
    
    if ($apps) {{
        $apps | ConvertTo-Json -Depth 3
    }} else {{
        "[]"
    }}
    """
    
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            # Limpiar posibles mensajes de PowerShell
            lines = [line for line in output.split('\n') if line.strip() and not line.strip().startswith('Windows PowerShell')]
            output = '\n'.join(lines)
            
            try:
                apps = json.loads(output)
                # Si es un solo objeto, convertirlo a lista
                if isinstance(apps, dict):
                    apps = [apps]
                return apps if apps else []
            except json.JSONDecodeError:
                return []
        else:
            return []
    except Exception as e:
        print(f"Error ejecutando búsqueda local: {e}")
        return []


def buscar_software_remoto(helper, hostname, nombre, publisher=""):
    """
    Busca software instalado en un equipo remoto
    
    Args:
        helper: Instancia de PsExecHelper
        hostname: Nombre del host remoto
        nombre: Nombre del software a buscar
        publisher: Publisher del software (opcional)
    
    Returns:
        list: Lista de software encontrado
    """
    ps_command = f"""
    $searchName = "{nombre}"
    $searchPublisher = "{publisher}"
    
    $apps = Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | 
      Where-Object {{ 
        ($_.DisplayName -like "*$searchName*") -and
        (($searchPublisher -eq "") -or ($_.Publisher -like "*$searchPublisher*"))
      }} | 
      Select-Object DisplayName, DisplayVersion, Publisher, UninstallString, PSChildName, InstallDate
    
    if ($apps) {{
        $apps | ConvertTo-Json -Depth 3
    }} else {{
        "[]"
    }}
    """
    
    result = helper.run_remote(hostname, ps_command, verbose=False)
    
    if result != "N/A":
        try:
            apps = json.loads(result)
            if isinstance(apps, dict):
                apps = [apps]
            return apps if apps else []
        except json.JSONDecodeError:
            return []
    return []


def mostrar_software_encontrado(apps):
    """
    Muestra el software encontrado en formato legible
    
    Args:
        apps: Lista de software encontrado
    """
    if not apps:
        print("\n❌ No se encontró software")
        return
    
    print(f"\n✅ Software encontrado ({len(apps)} aplicación/es):")
    print("=" * 100)
    print(f"{'Nombre':<50} {'Versión':<20} {'Publisher':<30}")
    print("=" * 100)
    
    for app in apps:
        nombre = app.get('DisplayName', 'N/A')
        version = app.get('DisplayVersion', 'N/A')
        publisher = app.get('Publisher', 'N/A')
        
        # Truncar si es muy largo
        nombre = nombre[:47] + "..." if len(nombre) > 50 else nombre
        version = version[:17] + "..." if len(version) > 20 else version
        publisher = publisher[:27] + "..." if len(publisher) > 30 else publisher
        
        print(f"{nombre:<50} {version:<20} {publisher:<30}")
    
    print("=" * 100)


def main():
    """Función principal"""
    clear_screen()
    config = load_config()
    
    print("=" * 60)
    print("🔍 BUSCAR SOFTWARE INSTALADO")
    print("=" * 60)
    
    # Preguntar si es local o remoto
    print("\n¿Dónde querés buscar el software?")
    print("1. En este equipo (local)")
    print("2. En un equipo remoto")
    opcion = input("\nOpción (1 o 2): ").strip()
    
    # Solicitar nombre del software
    nombre = input("\nNombre del software a buscar (ej: 'Dell Command' o 'Chrome'): ").strip()
    if not nombre:
        print("❌ Debes ingresar un nombre")
        input("\nPresioná ENTER para salir...")
        return
    
    # Solicitar publisher (opcional)
    publisher = input("Publisher del software (opcional, presionar Enter para omitir): ").strip()
    
    apps = []
    
    if opcion == "1":
        # Búsqueda local
        print(f"\n🔍 Buscando '{nombre}' en este equipo...")
        apps = buscar_software_local(nombre, publisher)
    elif opcion == "2":
        # Búsqueda remota
        hostname = input("\nHostname del equipo remoto (ej: NB036595): ").strip()
        if not hostname:
            print("❌ Debes ingresar un hostname")
            input("\nPresioná ENTER para salir...")
            return
        
        # Solicitar credenciales
        user, password = get_credentials()
        
        helper = PsExecHelper(
            psexec_path=config.get("psexec_path", "PsExec.exe"),
            remote_user=user,
            remote_pass=password
        )
        
        print(f"\n🔍 Buscando '{nombre}' en {hostname}...")
        apps = buscar_software_remoto(helper, hostname, nombre, publisher)
    else:
        print("❌ Opción inválida")
        input("\nPresioná ENTER para salir...")
        return
    
    # Mostrar resultados
    mostrar_software_encontrado(apps)
    
    # Guardar resultados en JSON si se encontró algo
    if apps:
        guardar = input("\n¿Deseás guardar los resultados en un archivo JSON? (S/N): ").strip().upper()
        if guardar == "S":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"software_encontrado_{timestamp}.json"
            
            os.makedirs("data/reports", exist_ok=True)
            filepath = os.path.join("data/reports", filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(apps, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Resultados guardados en: {filepath}")
    
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    main()

