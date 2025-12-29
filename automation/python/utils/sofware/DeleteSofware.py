"""
Script para eliminar software instalado en Windows
Funciona local o remotamente, soporta MSI y EXE
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


def buscar_software_local(nombre, publisher=""):
    """Busca software instalado localmente"""
    ps_command = f"""
    $searchName = "{nombre}"
    $searchPublisher = "{publisher}"
    
    $apps = Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | 
      Where-Object {{ 
        ($_.DisplayName -like "*$searchName*") -and
        (($searchPublisher -eq "") -or ($_.Publisher -like "*$searchPublisher*"))
      }} | 
      Select-Object DisplayName, DisplayVersion, Publisher, UninstallString, PSChildName
    
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
            lines = [line for line in output.split('\n') if line.strip() and not line.strip().startswith('Windows PowerShell')]
            output = '\n'.join(lines)
            
            try:
                apps = json.loads(output)
                if isinstance(apps, dict):
                    apps = [apps]
                return apps if apps else []
            except json.JSONDecodeError:
                return []
    except Exception:
        return []
    return []


def detener_procesos_local(nombre):
    """Detiene procesos relacionados con el software localmente"""
    ps_command = f"""
    $processes = Get-Process | Where-Object {{ 
      $_.ProcessName -like "*{nombre}*" -or
      $_.MainWindowTitle -like "*{nombre}*"
    }}
    if ($processes) {{
        $processes | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        "Procesos detenidos"
    }} else {{
        "No hay procesos ejecutándose"
    }}
    """
    
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_command],
            capture_output=True,
            timeout=30
        )
    except Exception:
        pass


def desinstalar_software_local(app):
    """
    Desinstala un software específico localmente
    
    Args:
        app: Diccionario con información del software (DisplayName, UninstallString, PSChildName)
    
    Returns:
        bool: True si se desinstaló correctamente
    """
    display_name = app.get('DisplayName', '')
    uninstall_string = app.get('UninstallString', '')
    product_code = app.get('PSChildName', '')
    
    print(f"\n🔧 Desinstalando: {display_name}")
    
    # Detener procesos primero
    detener_procesos_local(display_name)
    
    # Construir comando de desinstalación
    ps_command = f"""
    $displayName = "{display_name}"
    $uninstallString = "{uninstall_string}"
    $productCode = "{product_code}"
    
    $desinstalado = $false
    
    # Método 1: MSI
    if ($uninstallString -like "*msiexec*" -or $productCode -match '^\\{{[A-F0-9-]+\\}}$') {{
        if ($productCode -match '^\\{{[A-F0-9-]+\\}}$') {{
            $msiArgs = "/x $productCode /quiet /norestart"
            Write-Host "Ejecutando: msiexec $msiArgs"
            try {{
                $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
                $desinstalado = $true
            }} catch {{
                Write-Host "Error: $_"
            }}
        }} else {{
            $guid = ($uninstallString -split '/I')[-1].Trim()
            if ($guid -match '^\\{{[A-F0-9-]+\\}}$') {{
                $msiArgs = "/x $guid /quiet /norestart"
                Write-Host "Ejecutando: msiexec $msiArgs"
                try {{
                    $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
                    $desinstalado = $true
                }} catch {{
                    Write-Host "Error: $_"
                }}
            }}
        }}
    }} 
    # Método 2: EXE
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
            Write-Host "Ejecutando: $exePath $args"
            try {{
                if (Test-Path $exePath) {{
                    $process = Start-Process -FilePath $exePath -ArgumentList $args -Wait -PassThru -NoNewWindow
                    $desinstalado = $true
                }} else {{
                    Write-Host "No se encontró: $exePath"
                }}
            }} catch {{
                Write-Host "Error: $_"
            }}
        }}
    }}
    
    Start-Sleep -Seconds 5
    
    # Verificar desinstalación
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
    except Exception as e:
        print(f"  ⚠ Error durante desinstalación: {e}")
        return False


def desinstalar_software_remoto(helper, hostname, app):
    """
    Desinstala software en un equipo remoto
    
    Args:
        helper: Instancia de PsExecHelper
        hostname: Nombre del host remoto
        app: Diccionario con información del software
    
    Returns:
        bool: True si se desinstaló correctamente
    """
    display_name = app.get('DisplayName', '')
    uninstall_string = app.get('UninstallString', '')
    product_code = app.get('PSChildName', '')
    
    print(f"\n🔧 Desinstalando: {display_name} en {hostname}")
    
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
    
    # Método 1: MSI
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
    # Método 2: EXE
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
    
    result = helper.run_remote(hostname, ps_command, verbose=False, timeout=120)
    return "DESINSTALADO_OK" in result


def main():
    """Función principal"""
    clear_screen()
    config = load_config()
    
    print("=" * 60)
    print("🗑️  ELIMINAR SOFTWARE")
    print("=" * 60)
    
    # Preguntar si es local o remoto
    print("\n¿Dónde querés eliminar el software?")
    print("1. En este equipo (local)")
    print("2. En un equipo remoto")
    opcion = input("\nOpción (1 o 2): ").strip()
    
    # Solicitar nombre del software
    nombre = input("\nNombre del software a eliminar (ej: 'Dell Command' o 'Chrome'): ").strip()
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
        
        # Buscar remotamente
        ps_command = f"""
        $searchName = "{nombre}"
        $searchPublisher = "{publisher}"
        
        $apps = Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | 
          Where-Object {{ 
            ($_.DisplayName -like "*$searchName*") -and
            (($searchPublisher -eq "") -or ($_.Publisher -like "*$searchPublisher*"))
          }} | 
          Select-Object DisplayName, DisplayVersion, Publisher, UninstallString, PSChildName
        
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
                apps = apps if apps else []
            except json.JSONDecodeError:
                apps = []
    else:
        print("❌ Opción inválida")
        input("\nPresioná ENTER para salir...")
        return
    
    if not apps:
        print(f"\n❌ No se encontró software que coincida con '{nombre}'")
        input("\nPresioná ENTER para salir...")
        return
    
    # Mostrar software encontrado
    print(f"\n✅ Software encontrado ({len(apps)} aplicación/es):")
    print("=" * 80)
    for i, app in enumerate(apps, 1):
        print(f"{i}. {app.get('DisplayName', 'N/A')} - Versión: {app.get('DisplayVersion', 'N/A')}")
    print("=" * 80)
    
    # Confirmar eliminación
    confirmar = input("\n¿Deseás eliminar estas aplicaciones? (S/N): ").strip().upper()
    if confirmar not in ['S', 'Y', 'SI', 'YES']:
        print("Operación cancelada.")
        input("\nPresioná ENTER para salir...")
        return
    
    # Desinstalar
    resultados = []
    for app in apps:
        if opcion == "1":
            exito = desinstalar_software_local(app)
        else:
            exito = desinstalar_software_remoto(helper, hostname, app)
        
        resultados.append({
            "nombre": app.get('DisplayName', ''),
            "exito": exito
        })
        
        if exito:
            print(f"  ✅ {app.get('DisplayName', '')} desinstalado correctamente")
        else:
            print(f"  ⚠️  {app.get('DisplayName', '')} aún está instalado (puede requerir reinicio)")
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    exitosos = sum(1 for r in resultados if r['exito'])
    print(f"✅ Desinstalados exitosamente: {exitosos}/{len(resultados)}")
    
    if exitosos < len(resultados):
        print("\n⚠️  Algunas aplicaciones pueden requerir reinicio para completar la desinstalación")
    
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    main()

