"""
Script específico para eliminar Dell Command | Update y componentes relacionados
Basado en el playbook de Ansible desistalarDellComand.yml
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


def buscar_dell_command_local():
    """Busca aplicaciones de Dell Command instaladas localmente"""
    ps_command = """
    $dellApps = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
      Where-Object { 
        ($_.DisplayName -like "*Dell Command*Update*") -or
        ($_.DisplayName -like "*Dell Command*") -or
        ($_.DisplayName -like "*Dell Update*") -or
        ($_.Publisher -like "*Dell*" -and $_.DisplayName -like "*Update*")
      } | 
      Select-Object DisplayName, DisplayVersion, Publisher, UninstallString, PSChildName, InstallDate
    
    if ($dellApps) {
        $dellApps | ConvertTo-Json -Depth 3
    } else {
        "[]"
    }
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


def buscar_dell_command_remoto(helper, hostname):
    """Busca aplicaciones de Dell Command en un equipo remoto"""
    ps_command = """
    $dellApps = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
      Where-Object { 
        ($_.DisplayName -like "*Dell Command*Update*") -or
        ($_.DisplayName -like "*Dell Command*") -or
        ($_.DisplayName -like "*Dell Update*") -or
        ($_.Publisher -like "*Dell*" -and $_.DisplayName -like "*Update*")
      } | 
      Select-Object DisplayName, DisplayVersion, Publisher, UninstallString, PSChildName, InstallDate
    
    if ($dellApps) {
        $dellApps | ConvertTo-Json -Depth 3
    } else {
        "[]"
    }
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


def detener_servicios_dell_local():
    """Detiene servicios relacionados con Dell Command localmente"""
    ps_command = """
    $services = @("DellClientManagementService", "DellUpdateService", "DellCommandUpdateService")
    foreach ($service in $services) {
        $svc = Get-Service -Name $service -ErrorAction SilentlyContinue
        if ($svc) {
            Stop-Service -Name $service -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 2
    "Servicios detenidos"
    """
    
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_command],
            capture_output=True,
            timeout=30
        )
    except Exception:
        pass


def detener_procesos_dell_local():
    """Detiene procesos relacionados con Dell Command localmente"""
    ps_command = """
    $processes = Get-Process | Where-Object { 
      $_.ProcessName -like "*Dell*" -or
      $_.ProcessName -like "*DCU*" -or
      $_.MainWindowTitle -like "*Dell Command*"
    }
    if ($processes) {
        $processes | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        "Procesos detenidos"
    } else {
        "No hay procesos"
    }
    """
    
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_command],
            capture_output=True,
            timeout=30
        )
    except Exception:
        pass


def desinstalar_dell_command_local(app):
    """
    Desinstala una aplicación específica de Dell Command localmente
    
    Args:
        app: Diccionario con información del software
    
    Returns:
        bool: True si se desinstaló correctamente
    """
    display_name = app.get('DisplayName', '')
    uninstall_string = app.get('UninstallString', '')
    product_code = app.get('PSChildName', '')
    
    print(f"\n🔧 Desinstalando: {display_name}")
    
    ps_command = f"""
    $displayName = "{display_name.replace('"', '\\"')}"
    $uninstallString = "{uninstall_string.replace('"', '\\"')}"
    $productCode = "{product_code}"
    
    $desinstalado = $false
    
    # Método 1: Intentar con msiexec usando ProductCode
    if ($productCode -match '^\\{{[A-F0-9-]+\\}}$') {{
        $msiArgs = "/x $productCode /quiet /norestart"
        try {{
            $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
            Start-Sleep -Seconds 5
            
            $stillInstalled = Get-ItemProperty "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\$productCode" -ErrorAction SilentlyContinue
            if (-not $stillInstalled) {{
                Write-Host "DESINSTALADO_OK"
                exit
            }}
        }} catch {{
            Write-Host "Error msiexec: $_"
        }}
    }}
    
    # Método 2: Usar UninstallString directamente
    if ($uninstallString) {{
        $cleanUninstall = $uninstallString -replace '"', ''
        
        if ($cleanUninstall -like "*msiexec*") {{
            if ($cleanUninstall -match '\\{{[A-F0-9-]+\\}}') {{
                $guid = $matches[0]
                $msiArgs = "/x $guid /quiet /norestart"
                try {{
                    $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
                }} catch {{
                    Write-Host "Error: $_"
                }}
            }}
        }} elseif ($cleanUninstall -like "*.exe*") {{
            $exePath = ($cleanUninstall -split '\\.exe')[0] + '.exe'
            $existingArgs = ($cleanUninstall -split '\\.exe')[1]
            
            $args = if ($existingArgs) {{ 
                $existingArgs.Trim() + " /S /silent /quiet" 
            }} else {{ 
                "/S /silent /quiet /uninstall" 
            }}
            
            try {{
                if (Test-Path $exePath) {{
                    $process = Start-Process -FilePath $exePath -ArgumentList $args -Wait -PassThru -NoNewWindow
                }}
            }} catch {{
                Write-Host "Error: $_"
            }}
        }}
        
        Start-Sleep -Seconds 5
    }}
    
    # Verificar desinstalación final
    $finalCheck = Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | 
      Where-Object {{ $_.DisplayName -eq $displayName }}
    
    if (-not $finalCheck) {{
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


def desinstalar_dell_command_remoto(helper, hostname, app):
    """
    Desinstala aplicación de Dell Command en un equipo remoto
    
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
    
    # Detener servicios
    stop_services_cmd = """
    $services = @("DellClientManagementService", "DellUpdateService", "DellCommandUpdateService")
    foreach ($service in $services) {
        $svc = Get-Service -Name $service -ErrorAction SilentlyContinue
        if ($svc) {
            Stop-Service -Name $service -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 2
    """
    helper.run_remote(hostname, stop_services_cmd, verbose=False)
    
    # Detener procesos
    stop_processes_cmd = """
    $processes = Get-Process | Where-Object { 
      $_.ProcessName -like "*Dell*" -or
      $_.ProcessName -like "*DCU*" -or
      $_.MainWindowTitle -like "*Dell Command*"
    }
    if ($processes) {
        $processes | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
    }
    """
    helper.run_remote(hostname, stop_processes_cmd, verbose=False)
    
    # Desinstalar
    ps_command = f"""
    $displayName = "{display_name.replace('"', '\\"')}"
    $uninstallString = "{uninstall_string.replace('"', '\\"')}"
    $productCode = "{product_code}"
    
    # Método 1: Intentar con msiexec usando ProductCode
    if ($productCode -match '^\\{{[A-F0-9-]+\\}}$') {{
        $msiArgs = "/x $productCode /quiet /norestart"
        try {{
            $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
            Start-Sleep -Seconds 5
            
            $stillInstalled = Get-ItemProperty "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\$productCode" -ErrorAction SilentlyContinue
            if (-not $stillInstalled) {{
                Write-Host "DESINSTALADO_OK"
                exit
            }}
        }} catch {{
            Write-Host "Error msiexec: $_"
        }}
    }}
    
    # Método 2: Usar UninstallString
    if ($uninstallString) {{
        $cleanUninstall = $uninstallString -replace '"', ''
        
        if ($cleanUninstall -like "*msiexec*") {{
            if ($cleanUninstall -match '\\{{[A-F0-9-]+\\}}') {{
                $guid = $matches[0]
                $msiArgs = "/x $guid /quiet /norestart"
                try {{
                    $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
                }} catch {{
                    Write-Host "Error: $_"
                }}
            }}
        }} elseif ($cleanUninstall -like "*.exe*") {{
            $exePath = ($cleanUninstall -split '\\.exe')[0] + '.exe'
            $existingArgs = ($cleanUninstall -split '\\.exe')[1]
            
            $args = if ($existingArgs) {{ 
                $existingArgs.Trim() + " /S /silent /quiet" 
            }} else {{ 
                "/S /silent /quiet /uninstall" 
            }}
            
            try {{
                if (Test-Path $exePath) {{
                    $process = Start-Process -FilePath $exePath -ArgumentList $args -Wait -PassThru -NoNewWindow
                }}
            }} catch {{
                Write-Host "Error: $_"
            }}
        }}
        
        Start-Sleep -Seconds 5
    }}
    
    # Verificar
    $finalCheck = Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | 
      Where-Object {{ $_.DisplayName -eq $displayName }}
    
    if (-not $finalCheck) {{
        Write-Host "DESINSTALADO_OK"
    }} else {{
        Write-Host "AUN_INSTALADO"
    }}
    """
    
    result = helper.run_remote(hostname, ps_command, verbose=False, timeout=120)
    return "DESINSTALADO_OK" in result


def limpiar_archivos_residuales_local():
    """Limpia archivos residuales de Dell Command localmente"""
    ps_command = """
    $paths = @(
        "$env:ProgramFiles\Dell\CommandUpdate",
        "$env:ProgramFiles(x86)\Dell\CommandUpdate",
        "$env:ProgramData\Dell\CommandUpdate",
        "$env:LOCALAPPDATA\Dell\CommandUpdate"
    )
    
    foreach ($path in $paths) {
        if (Test-Path $path) {
            Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    "Limpieza completada"
    """
    
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_command],
            capture_output=True,
            timeout=30
        )
    except Exception:
        pass


def main():
    """Función principal"""
    clear_screen()
    config = load_config()
    
    print("=" * 60)
    print("🗑️  ELIMINAR DELL COMMAND | UPDATE")
    print("=" * 60)
    
    # Preguntar si es local o remoto
    print("\n¿Dónde querés eliminar Dell Command?")
    print("1. En este equipo (local)")
    print("2. En un equipo remoto")
    opcion = input("\nOpción (1 o 2): ").strip()
    
    apps = []
    
    if opcion == "1":
        # Búsqueda local
        print("\n🔍 Buscando aplicaciones de Dell Command en este equipo...")
        apps = buscar_dell_command_local()
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
        
        print(f"\n🔍 Buscando aplicaciones de Dell Command en {hostname}...")
        apps = buscar_dell_command_remoto(helper, hostname)
    else:
        print("❌ Opción inválida")
        input("\nPresioná ENTER para salir...")
        return
    
    if not apps:
        print("\n❌ No se encontró Dell Command | Update instalado")
        input("\nPresioná ENTER para salir...")
        return
    
    # Mostrar software encontrado
    print(f"\n✅ Aplicaciones de Dell Command encontradas ({len(apps)}):")
    print("=" * 80)
    for i, app in enumerate(apps, 1):
        print(f"{i}. {app.get('DisplayName', 'N/A')} - Versión: {app.get('DisplayVersion', 'N/A')}")
        print(f"   Publisher: {app.get('Publisher', 'N/A')}")
    print("=" * 80)
    
    # Confirmar eliminación
    confirmar = input("\n¿Deseás eliminar estas aplicaciones de Dell Command? (S/N): ").strip().upper()
    if confirmar not in ['S', 'Y', 'SI', 'YES']:
        print("Operación cancelada.")
        input("\nPresioná ENTER para salir...")
        return
    
    # Detener servicios y procesos antes de desinstalar
    if opcion == "1":
        print("\n🛑 Deteniendo servicios de Dell Command...")
        detener_servicios_dell_local()
        print("🛑 Deteniendo procesos de Dell Command...")
        detener_procesos_dell_local()
    
    # Desinstalar cada aplicación
    resultados = []
    for app in apps:
        if opcion == "1":
            exito = desinstalar_dell_command_local(app)
        else:
            exito = desinstalar_dell_command_remoto(helper, hostname, app)
        
        resultados.append({
            "nombre": app.get('DisplayName', ''),
            "exito": exito
        })
        
        if exito:
            print(f"  ✅ {app.get('DisplayName', '')} desinstalado correctamente")
        else:
            print(f"  ⚠️  {app.get('DisplayName', '')} aún está instalado (puede requerir reinicio)")
    
    # Limpiar archivos residuales (solo local por ahora)
    if opcion == "1":
        print("\n🧹 Limpiando archivos residuales...")
        limpiar_archivos_residuales_local()
    
    # Verificación final
    print("\n🔍 Verificando desinstalación final...")
    time.sleep(3)
    
    if opcion == "1":
        apps_finales = buscar_dell_command_local()
    else:
        apps_finales = buscar_dell_command_remoto(helper, hostname)
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    exitosos = sum(1 for r in resultados if r['exito'])
    print(f"✅ Desinstalados exitosamente: {exitosos}/{len(resultados)}")
    
    if apps_finales:
        print(f"\n⚠️  Aún quedan {len(apps_finales)} aplicación/es de Dell Command instaladas:")
        for app in apps_finales:
            print(f"  - {app.get('DisplayName', 'N/A')}")
        print("\n💡 Puede requerir reinicio para completar la desinstalación")
    else:
        print("\n✅ Dell Command | Update desinstalado completamente")
    
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    main()

