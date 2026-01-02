"""
Script para listar todos los softwares instalados y permitir eliminarlos interactivamente
Incluye filtrado, búsqueda y selección múltiple
"""
import sys
import os
import subprocess
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.psexec_helper import PsExecHelper
from utils.common import clear_screen, load_config, get_credentials


def listar_software_local():
    """
    Lista todos los softwares instalados localmente
    
    Returns:
        list: Lista de software instalado
    """
    ps_command = """
    $apps = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
      Where-Object { $_.DisplayName } |
      Select-Object DisplayName, DisplayVersion, Publisher, UninstallString, PSChildName, InstallDate |
      Sort-Object DisplayName
    
    $apps | ConvertTo-Json -Depth 3
    """
    
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            lines = [line for line in output.split('\n') if line.strip() and not line.strip().startswith('Windows PowerShell')]
            output = '\n'.join(lines)
            
            try:
                apps = json.loads(output)
                if isinstance(apps, dict):
                    apps = [apps]
                return apps if apps else []
            except json.JSONDecodeError:
                return []
    except Exception as e:
        print(f"Error listando software: {e}")
        return []
    return []


def listar_software_remoto(helper, hostname):
    """
    Lista todos los softwares instalados en un equipo remoto
    
    Args:
        helper: Instancia de PsExecHelper
        hostname: Nombre del host remoto
    
    Returns:
        list: Lista de software instalado
    """
    ps_command = """
    $apps = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
      Where-Object { $_.DisplayName } |
      Select-Object DisplayName, DisplayVersion, Publisher, UninstallString, PSChildName, InstallDate |
      Sort-Object DisplayName
    
    $apps | ConvertTo-Json -Depth 3
    """
    
    result = helper.run_remote(hostname, ps_command, verbose=False, timeout=60)
    if result != "N/A":
        try:
            apps = json.loads(result)
            if isinstance(apps, dict):
                apps = [apps]
            return apps if apps else []
        except json.JSONDecodeError:
            return []
    return []


def filtrar_software(apps, filtro):
    """
    Filtra software por nombre o publisher
    
    Args:
        apps: Lista de software
        filtro: Texto a buscar en nombre o publisher
    
    Returns:
        list: Software filtrado
    """
    if not filtro:
        return apps
    
    filtro_lower = filtro.lower()
    return [
        app for app in apps
        if filtro_lower in app.get('DisplayName', '').lower() or
           filtro_lower in app.get('Publisher', '').lower()
    ]


def mostrar_software(apps, pagina=1, por_pagina=20):
    """
    Muestra software en formato de tabla paginada
    
    Args:
        apps: Lista de software
        pagina: Número de página (empezando en 1)
        por_pagina: Cantidad de elementos por página
    """
    total = len(apps)
    inicio = (pagina - 1) * por_pagina
    fin = min(inicio + por_pagina, total)
    apps_pagina = apps[inicio:fin]
    
    print(f"\n📦 Software instalado (Mostrando {inicio + 1}-{fin} de {total})")
    print("=" * 110)
    print(f"{'#':<5} {'Nombre':<50} {'Versión':<20} {'Publisher':<30}")
    print("=" * 110)
    
    for i, app in enumerate(apps_pagina, start=inicio + 1):
        nombre = app.get('DisplayName', 'N/A')
        version = app.get('DisplayVersion', 'N/A')
        publisher = app.get('Publisher', 'N/A')
        
        # Truncar si es muy largo
        nombre = nombre[:47] + "..." if len(nombre) > 50 else nombre
        version = version[:17] + "..." if len(version) > 20 else version
        publisher = publisher[:27] + "..." if len(publisher) > 30 else publisher
        
        print(f"{i:<5} {nombre:<50} {version:<20} {publisher:<30}")
    
    print("=" * 110)
    
    # Información de paginación
    total_paginas = (total + por_pagina - 1) // por_pagina
    if total_paginas > 1:
        print(f"Página {pagina} de {total_paginas} (usá 's' para siguiente, 'a' para anterior)")
    
    return apps_pagina, total_paginas


def desinstalar_software_local(app):
    """Desinstala un software localmente"""
    display_name = app.get('DisplayName', '')
    uninstall_string = app.get('UninstallString', '')
    product_code = app.get('PSChildName', '')
    
    # Detener procesos
    stop_cmd = f"""
    $processes = Get-Process | Where-Object {{ 
      $_.ProcessName -like "*{display_name}*" -or
      $_.MainWindowTitle -like "*{display_name}*"
    }}
    if ($processes) {{
        $processes | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }}
    """
    
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", stop_cmd],
            capture_output=True,
            timeout=30
        )
    except Exception:
        pass
    
    # Desinstalar
    ps_command = f"""
    $displayName = "{display_name.replace('"', '\\"')}"
    $uninstallString = "{uninstall_string.replace('"', '\\"')}"
    $productCode = "{product_code}"
    
    # MSI
    if ($uninstallString -like "*msiexec*" -or $productCode -match '^\\{{[A-F0-9-]+\\}}$') {{
        if ($productCode -match '^\\{{[A-F0-9-]+\\}}$') {{
            $msiArgs = "/x $productCode /quiet /norestart"
            try {{
                $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
            }} catch {{
                Write-Host "Error: $_"
            }}
        }}
    }} 
    # EXE
    else {{
        $cleanUninstall = $uninstallString -replace '"', ''
        if ($cleanUninstall -like "*.exe*") {{
            $exePath = ($cleanUninstall -split '\\.exe')[0] + '.exe'
            $args = ($cleanUninstall -split '\\.exe')[1]
            if ($args) {{
                $args = $args.Trim() + " /S /silent /quiet"
            }} else {{
                $args = "/S /silent /quiet"
            }}
            try {{
                if (Test-Path $exePath) {{
                    $process = Start-Process -FilePath $exePath -ArgumentList $args -Wait -PassThru -NoNewWindow
                }}
            }} catch {{
                Write-Host "Error: $_"
            }}
        }}
    }}
    
    Start-Sleep -Seconds 5
    
    # Verificar
    $stillInstalled = Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | 
      Where-Object {{ $_.DisplayName -eq $displayName }}
    
    if (-not $stillInstalled) {{
        Write-Host "DESINSTALADO_OK"
    }} else {{
        Write-Host "AUN_INSTALADO"
    }}
    """
    
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = result.stdout.strip()
        return "DESINSTALADO_OK" in output
    except Exception:
        return False


def desinstalar_software_remoto(helper, hostname, app):
    """Desinstala un software en un equipo remoto"""
    display_name = app.get('DisplayName', '')
    uninstall_string = app.get('UninstallString', '')
    product_code = app.get('PSChildName', '')
    
    # Detener procesos
    stop_cmd = f"""
    $processes = Get-Process | Where-Object {{ 
      $_.ProcessName -like "*{display_name}*" -or
      $_.MainWindowTitle -like "*{display_name}*"
    }}
    if ($processes) {{
        $processes | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }}
    """
    helper.run_remote(hostname, stop_cmd, verbose=False)
    
    # Desinstalar
    ps_command = f"""
    $displayName = "{display_name.replace('"', '\\"')}"
    $uninstallString = "{uninstall_string.replace('"', '\\"')}"
    $productCode = "{product_code}"
    
    if ($uninstallString -like "*msiexec*" -or $productCode -match '^\\{{[A-F0-9-]+\\}}$') {{
        if ($productCode -match '^\\{{[A-F0-9-]+\\}}$') {{
            $msiArgs = "/x $productCode /quiet /norestart"
            try {{
                $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
            }} catch {{
                Write-Host "Error: $_"
            }}
        }}
    }} else {{
        $cleanUninstall = $uninstallString -replace '"', ''
        if ($cleanUninstall -like "*.exe*") {{
            $exePath = ($cleanUninstall -split '\\.exe')[0] + '.exe'
            $args = ($cleanUninstall -split '\\.exe')[1]
            if ($args) {{
                $args = $args.Trim() + " /S /silent /quiet"
            }} else {{
                $args = "/S /silent /quiet"
            }}
            try {{
                if (Test-Path $exePath) {{
                    $process = Start-Process -FilePath $exePath -ArgumentList $args -Wait -PassThru -NoNewWindow
                }}
            }} catch {{
                Write-Host "Error: $_"
            }}
        }}
    }}
    
    Start-Sleep -Seconds 5
    
    $stillInstalled = Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | 
      Where-Object {{ $_.DisplayName -eq $displayName }}
    
    if (-not $stillInstalled) {{
        Write-Host "DESINSTALADO_OK"
    }} else {{
        Write-Host "AUN_INSTALADO"
    }}
    """
    
    result = helper.run_remote(hostname, ps_command, verbose=False, timeout=120)
    return "DESINSTALADO_OK" in result


def main():
    """Función principal"""
    clear_screen()
    config = load_config()
    
    print("=" * 60)
    print("📦 LISTAR Y ELIMINAR SOFTWARE")
    print("=" * 60)
    
    # Preguntar si es local o remoto
    print("\n¿Dónde querés listar el software?")
    print("1. En este equipo (local)")
    print("2. En un equipo remoto")
    opcion = input("\nOpción (1 o 2): ").strip()
    
    apps = []
    
    if opcion == "1":
        print("\n🔍 Obteniendo lista de software instalado...")
        apps = listar_software_local()
    elif opcion == "2":
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
        
        print(f"\n🔍 Obteniendo lista de software instalado en {hostname}...")
        apps = listar_software_remoto(helper, hostname)
    else:
        print("❌ Opción inválida")
        input("\nPresioná ENTER para salir...")
        return
    
    if not apps:
        print("\n❌ No se encontró software instalado")
        input("\nPresioná ENTER para salir...")
        return
    
    print(f"\n✅ Se encontraron {len(apps)} aplicaciones instaladas")
    
    # Aplicar filtro si se desea
    apps_filtrados = apps.copy()
    filtro = ""
    pagina = 1
    por_pagina = 20
    
    while True:
        clear_screen()
        print("=" * 60)
        print("📦 LISTAR Y ELIMINAR SOFTWARE")
        print("=" * 60)
        
        if filtro:
            print(f"\n🔍 Filtro activo: '{filtro}' ({len(apps_filtrados)} resultados)")
            apps_mostrados = filtrar_software(apps_filtrados, filtro)
        else:
            apps_mostrados = apps_filtrados
        
        apps_pagina, total_paginas = mostrar_software(apps_mostrados, pagina, por_pagina)
        
        print("\n📋 Comandos disponibles:")
        print("  - Ingresá un número para seleccionar software para eliminar")
        print("  - 'f' = Filtrar/Buscar")
        print("  - 'r' = Restablecer filtro")
        print("  - 's' = Siguiente página")
        print("  - 'a' = Anterior página")
        print("  - 'g' = Guardar lista en archivo")
        print("  - 'q' = Salir")
        
        if filtro:
            print(f"\n💡 Para buscar otro texto, usá 'f' y luego 'r' para ver todo")
        
        comando = input("\nIngresá comando o número: ").strip().lower()
        
        if comando == 'q':
            break
        elif comando == 'f':
            nuevo_filtro = input("\nIngresá texto para filtrar (nombre o publisher): ").strip()
            if nuevo_filtro:
                filtro = nuevo_filtro
                pagina = 1
        elif comando == 'r':
            filtro = ""
            pagina = 1
        elif comando == 's':
            if pagina < total_paginas:
                pagina += 1
        elif comando == 'a':
            if pagina > 1:
                pagina -= 1
        elif comando == 'g':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lista_software_{timestamp}.json"
            
            os.makedirs("data/reports", exist_ok=True)
            filepath = os.path.join("data/reports", filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(apps_mostrados, f, indent=4, ensure_ascii=False)
            
            print(f"\n✅ Lista guardada en: {filepath}")
            input("\nPresioná ENTER para continuar...")
        elif comando.isdigit():
            indice = int(comando) - 1
            inicio = (pagina - 1) * por_pagina
            
            if 0 <= indice < len(apps_mostrados):
                app_seleccionado = apps_mostrados[inicio + indice]
                nombre = app_seleccionado.get('DisplayName', 'N/A')
                version = app_seleccionado.get('DisplayVersion', 'N/A')
                publisher = app_seleccionado.get('Publisher', 'N/A')
                
                print(f"\n📦 Software seleccionado:")
                print(f"  Nombre: {nombre}")
                print(f"  Versión: {version}")
                print(f"  Publisher: {publisher}")
                
                confirmar = input(f"\n¿Deseás eliminar '{nombre}'? (S/N): ").strip().upper()
                if confirmar in ['S', 'Y', 'SI', 'YES']:
                    print(f"\n🔧 Eliminando {nombre}...")
                    
                    if opcion == "1":
                        exito = desinstalar_software_local(app_seleccionado)
                    else:
                        exito = desinstalar_software_remoto(helper, hostname, app_seleccionado)
                    
                    if exito:
                        print(f"✅ {nombre} desinstalado correctamente")
                        # Remover de la lista
                        if app_seleccionado in apps_filtrados:
                            apps_filtrados.remove(app_seleccionado)
                        if filtro:
                            apps_mostrados = filtrar_software(apps_filtrados, filtro)
                    else:
                        print(f"⚠️  {nombre} aún está instalado (puede requerir reinicio)")
                    
                    input("\nPresioná ENTER para continuar...")
            else:
                print(f"\n❌ Número inválido. Debe estar entre 1 y {len(apps_pagina)}")
                input("\nPresioná ENTER para continuar...")
        else:
            print("\n❌ Comando no reconocido")
            input("\nPresioná ENTER para continuar...")
    
    print("\n👋 ¡Hasta luego!")


if __name__ == "__main__":
    main()

