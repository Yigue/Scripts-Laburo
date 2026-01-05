"""
Módulo para obtener especificaciones del sistema remoto
Corresponde a la opción 1 del menú
"""
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)
from utils.remote_executor import RemoteExecutor


SCRIPT_SYSTEM_INFO = '''
# Redirigir Write-Host a Write-Output (ejecución silenciosa)
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
$null = $true  # Silenciar definición de función

Write-Output ">>> INICIO RECOLECCIÓN DE DATOS <<<"

try {
    $systemInfo = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
    $biosInfo = Get-CimInstance -ClassName Win32_BIOS -ErrorAction SilentlyContinue
    $processorInfo = Get-CimInstance -ClassName Win32_Processor -ErrorAction SilentlyContinue
    $osInfo = Get-WmiObject -Class Win32_OperatingSystem -ErrorAction SilentlyContinue
    $serialNumber = (Get-WmiObject -Class Win32_BIOS -ErrorAction SilentlyContinue).SerialNumber
    
    if (!$serialNumber) { $serialNumber = "No disponible" }

    # Obtener parche de actualizacion
    $path = "Registry::HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\Packages"
    $pkgs = Get-ChildItem $path -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "Package_for_RollupFix" } | Sort-Object Name -Descending | Select-Object -First 1

    # Disco
    $diskInfo = Get-CimInstance -ClassName Win32_DiskDrive -ErrorAction SilentlyContinue | Select-Object Model, @{Name="SizeGB";Expression={[math]::round($_.Size / 1GB, 2)}}
    $logicalDisks = Get-CimInstance -ClassName Win32_LogicalDisk -ErrorAction SilentlyContinue | Where-Object { $_.DriveType -eq 3 }

    # Red
    $networkAdapters = Get-CimInstance -ClassName Win32_NetworkAdapterConfiguration -ErrorAction SilentlyContinue | Where-Object { $_.IPEnabled -eq $true }
    $wifiAdapter = $networkAdapters | Where-Object { $_.Description -match "Wi-Fi|Wireless" }
    $wifiIP = if ($wifiAdapter -and $wifiAdapter.IPAddress) { $wifiAdapter.IPAddress -join ', ' } else { "No conectado" }
    $ethernetAdapter = $networkAdapters | Where-Object { $_.Description -notmatch "Wi-Fi|Wireless" }
    $ethernetIP = if ($ethernetAdapter -and $ethernetAdapter.IPAddress) { $ethernetAdapter.IPAddress -join ', ' } else { "No conectado" }

    # Version Windows
    $displayVersion = Get-ItemPropertyValue -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion' -Name DisplayVersion -ErrorAction SilentlyContinue
    $buildNumber = if ($osInfo) { $osInfo.BuildNumber } else { "N/A" }
    $versionWinver = if ($pkgs) { $pkgs.PSChildName -replace ".*~", "" } else { "N/A" }

    # Fecha instalacion
    $formattedInstallDate = "N/A"
    if ($osInfo -and $osInfo.InstallDate) {
        $formattedInstallDate = [Management.ManagementDateTimeConverter]::ToDateTime($osInfo.InstallDate).ToString("dd/MM/yyyy HH:mm:ss")
    }

    # Espacio en disco
    $diskC = $logicalDisks | Where-Object { $_.DeviceID -eq "C:" }
    $freeSpaceGB = if ($diskC) { [math]::round($diskC.FreeSpace / 1GB, 2) } else { "N/A" }
    $totalSpaceGB = if ($diskC) { [math]::round($diskC.Size / 1GB, 2) } else { "N/A" }

    Write-Host "========================================================="
    Write-Host "             ESPECIFICACIONES DEL SISTEMA"
    Write-Host "========================================================="
    Write-Host "Nombre del equipo     : $($systemInfo.Name)"
    Write-Host "Modelo del equipo     : $($systemInfo.Model)"
    Write-Host "Fabricante            : $($systemInfo.Manufacturer)"
    Write-Host "Numero de Serie       : $serialNumber"
    Write-Host "Procesador            : $($processorInfo.Name)"
    Write-Host "RAM (GB)              : $([math]::round($systemInfo.TotalPhysicalMemory / 1GB, 2))"
    Write-Host "Version BIOS          : $($biosInfo.SMBIOSBIOSVersion)"
    Write-Host "Sistema Operativo     : $($osInfo.Caption)"
    Write-Host "Version Windows       : $displayVersion (Build $buildNumber)"
    Write-Host "Parche                : $versionWinver"
    Write-Host "Fecha Instalacion     : $formattedInstallDate"
    Write-Host "IP Wi-Fi              : $wifiIP"
    Write-Host "IP Ethernet           : $ethernetIP"
    Write-Host "========================================================="
    Write-Host "                 INFORMACION DEL DISCO"
    Write-Host "========================================================="
    Write-Host "Disco C: Total        : $totalSpaceGB GB"
    Write-Host "Disco C: Libre        : $freeSpaceGB GB"

    if ($diskInfo) {
        $diskInfo | ForEach-Object {
            Write-Host "Modelo Disco          : $($_.Model)"
            Write-Host "Tamano Disco          : $($_.SizeGB) GB"
        }
    }
} catch {
    Write-Output "❌ ERROR EN POWERSHELL: $($_.Exception.Message)"
    Write-Output "StackTrace: $($_.ScriptStackTrace)"
}

Write-Output ">>> FIN RECOLECCIÓN DE DATOS <<<"
'''

SCRIPT_BATTERY_INFO = '''
# Redirigir Write-Host a Write-Output
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}

try {
    $batteryXml = "$env:TEMP\\battery.xml"
    powercfg /batteryreport /xml /output $batteryXml 2>$null | Out-Null
    
    if (Test-Path $batteryXml) {
        [xml]$xml = Get-Content $batteryXml
        
        $designed = $xml.BatteryReport.Batteries.Battery.DesignCapacity
        $full = $xml.BatteryReport.Batteries.Battery.FullChargeCapacity
        
        if ($designed -and $full -and $designed -gt 0) {
            $health = [math]::Round(($full / $designed) * 100, 2)
            
            if ($health -ge 90) { $status = "Excelente" }
            elseif ($health -ge 70) { $status = "Buena" }
            elseif ($health -ge 50) { $status = "Regular" }
            else { $status = "Mala" }
            
            Write-Host "========================================================="
            Write-Host "                  ESTADO DE BATERIA"
            Write-Host "========================================================="
            Write-Host "Capacidad Disenada    : $designed mWh"
            Write-Host "Capacidad Actual      : $full mWh"
            Write-Host "Salud de Bateria      : $health %"
            Write-Host "Estado                : $status"
        } else {
            Write-Output "No se pudo obtener informacion de bateria"
        }
        
        Remove-Item $batteryXml -Force -ErrorAction SilentlyContinue
    }
} catch {
    Write-Output "Error obteniendo info de bateria: $($_.Exception.Message)"
}
'''


def ejecutar(executor: RemoteExecutor, hostname: str):
    """
    Obtiene y muestra las especificaciones del sistema remoto
    
    Args:
        executor: Instancia de RemoteExecutor
        hostname: Nombre del equipo remoto
    """
    print(f"\n📊 Obteniendo especificaciones de {hostname}...")
    print()
    
    try:
        # Ejecutar script de info del sistema
        print("⏳ Ejecutando comando remoto...")
        result = executor.run_script_block(hostname, SCRIPT_SYSTEM_INFO, timeout=60, verbose=True)
        
        # Debug: mostrar información detallada si no hay resultado
        if not result or not result.strip():
            # Obtener el resultado completo para diagnóstico
            full_result = executor.execute_ps(hostname, SCRIPT_SYSTEM_INFO, timeout=60, verbose=False)
            error = executor.get_last_error()
            
            print("\n" + "=" * 60)
            print("❌ ERROR OBTENIENDO INFORMACIÓN DEL SISTEMA")
            print("=" * 60)
            print(f"\n📊 DIAGNÓSTICO:")
            print(f"   • Success: {full_result.success}")
            print(f"   • Return Code: {full_result.return_code}")
            print(f"   • Método usado: {full_result.method_used}")
            print(f"   • Longitud stdout: {len(full_result.stdout) if full_result.stdout else 0} caracteres")
            print(f"   • Longitud stderr: {len(full_result.stderr) if full_result.stderr else 0} caracteres")
            
            if full_result.stdout:
                print(f"\n   📝 Contenido de stdout (primeros 200 chars):")
                print(f"   {repr(full_result.stdout[:200])}")
            
            if full_result.stderr:
                print(f"\n   ⚠️ Contenido de stderr:")
                print(f"   {full_result.stderr}")
            
            if error:
                print(f"\n   🔴 Error reportado:")
                print(f"   {error}")
            
            if not full_result.stdout and not full_result.stderr:
                print("\n   ⚠️ No se recibió ninguna salida (ni stdout ni stderr)")
                print("   Esto puede indicar que el script se ejecutó pero no produjo salida")
            
            print("\n" + "=" * 60)
            print("POSIBLES CAUSAS:")
            print("=" * 60)
            print("   • El script se ejecutó pero Write-Host no se capturó correctamente")
            print("   • Problemas con la captura de streams de información en pypsrp")
            print("   • WinRM no está habilitado en el equipo remoto")
            print("   • Problemas de conectividad de red")
            print("   • Permisos insuficientes")
            print("\nPara verificar:")
            print(f"   • Probar: Test-WSMan {hostname}")
            print(f"   • Verificar: Enable-PSRemoting -Force (en el equipo remoto)")
            print("=" * 60)
            print()
            input("Presioná ENTER para continuar...")
            return
        
        # Si hay resultado, mostrarlo
        if result and result.strip():
            print("\n" + "=" * 60)
            print(result)
            print("=" * 60)
        
        # Si es notebook (empieza con N), obtener info de batería
        if hostname.upper().startswith('N'):
            print()
            print("🔋 Obteniendo información de batería...")
            battery_result = executor.run_script_block(hostname, SCRIPT_BATTERY_INFO, timeout=30, verbose=False)
            if battery_result and battery_result != "(sin salida)":
                print(battery_result)
            else:
                print("   (No se pudo obtener información de batería)")
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    input("Presioná ENTER para continuar...")


def main():
    """Función principal para ejecución standalone"""
    from utils.common import clear_screen
    
    clear_screen()
    print("=" * 60)
    print("📊 ESPECIFICACIONES DEL SISTEMA")
    print("=" * 60)
    
    hostname = input("\nInventario: ").strip()
    if not hostname:
        print("❌ Debe ingresar un inventario")
        return
    
    executor = RemoteExecutor()
    
    # Verificar conexión
    conn = executor.test_connection(hostname)
    if not conn["ready"]:
        print(f"\n❌ No se pudo conectar a {hostname}")
        input("\nPresioná ENTER para salir...")
        return
    
    ejecutar(executor, hostname)


if __name__ == "__main__":
    main()

