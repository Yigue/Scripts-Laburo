"""
Módulo para obtener especificaciones del sistema remoto
Corresponde a la opción 1 del menú
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.winrm_executor import WinRMExecutor


SCRIPT_SYSTEM_INFO = '''
$systemInfo = Get-CimInstance -ClassName Win32_ComputerSystem
$biosInfo = Get-CimInstance -ClassName Win32_BIOS
$processorInfo = Get-CimInstance -ClassName Win32_Processor
$osInfo = Get-WmiObject -Class Win32_OperatingSystem
$serialNumber = Get-WmiObject -Class Win32_BIOS | Select-Object -ExpandProperty SerialNumber

# Obtener parche de actualizacion
$path = "Registry::HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\Packages"
$pkgs = Get-ChildItem $path -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "Package_for_RollupFix" } | Sort-Object Name -Descending | Select-Object -First 1

# Disco
$diskInfo = Get-CimInstance -ClassName Win32_DiskDrive | Select-Object Model, @{Name="SizeGB";Expression={[math]::round($_.Size / 1GB, 2)}}
$logicalDisks = Get-CimInstance -ClassName Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 }

# Red
$networkAdapters = Get-CimInstance -ClassName Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled -eq $true }
$wifiAdapter = $networkAdapters | Where-Object { $_.Description -match "Wi-Fi|Wireless" }
$wifiIP = if ($wifiAdapter -and $wifiAdapter.IPAddress) { $wifiAdapter.IPAddress -join ', ' } else { "No conectado" }
$ethernetAdapter = $networkAdapters | Where-Object { $_.Description -notmatch "Wi-Fi|Wireless" }
$ethernetIP = if ($ethernetAdapter -and $ethernetAdapter.IPAddress) { $ethernetAdapter.IPAddress -join ', ' } else { "No conectado" }

# Version Windows
$displayVersion = Get-ItemPropertyValue -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion' -Name DisplayVersion -ErrorAction SilentlyContinue
$buildNumber = $osInfo.BuildNumber
$versionWinver = if ($pkgs) { $pkgs.PSChildName -replace ".*~", "" } else { "N/A" }

# Fecha instalacion
$windowsInstallDate = (Get-WmiObject -Class Win32_OperatingSystem).InstallDate
$formattedInstallDate = [Management.ManagementDateTimeConverter]::ToDateTime($windowsInstallDate).ToString("dd/MM/yyyy HH:mm:ss")

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

$diskInfo | ForEach-Object {
    Write-Host "Modelo Disco          : $($_.Model)"
    Write-Host "Tamano Disco          : $($_.SizeGB) GB"
}
'''

SCRIPT_BATTERY_INFO = '''
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
            Write-Host "No se pudo obtener informacion de bateria"
        }
        
        Remove-Item $batteryXml -Force -ErrorAction SilentlyContinue
    }
} catch {
    Write-Host "Error obteniendo info de bateria: $_"
}
'''


def ejecutar(executor: WinRMExecutor, hostname: str):
    """
    Obtiene y muestra las especificaciones del sistema remoto
    
    Args:
        executor: Instancia de WinRMExecutor
        hostname: Nombre del equipo remoto
    """
    print(f"\n📊 Obteniendo especificaciones de {hostname}...")
    print()
    
    # Ejecutar script de info del sistema
    result = executor.run_script_block(hostname, SCRIPT_SYSTEM_INFO, timeout=60)
    
    if result:
        print(result)
    else:
        print("❌ Error obteniendo información del sistema")
        return
    
    # Si es notebook (empieza con N), obtener info de batería
    if hostname.upper().startswith('N'):
        print()
        battery_result = executor.run_script_block(hostname, SCRIPT_BATTERY_INFO, timeout=30)
        if battery_result:
            print(battery_result)
    
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
    
    executor = WinRMExecutor()
    
    # Verificar conexión
    conn = executor.test_connection(hostname)
    if not conn["ready"]:
        print(f"\n❌ No se pudo conectar a {hostname}")
        input("\nPresioná ENTER para salir...")
        return
    
    ejecutar(executor, hostname)


if __name__ == "__main__":
    main()

