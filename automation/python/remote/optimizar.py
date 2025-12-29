"""
Módulo para optimizar equipos remotos
Corresponde a la opción 3 del menú
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.winrm_executor import WinRMExecutor


SCRIPT_OPTIMIZAR = '''
Write-Host "Iniciando optimizacion del sistema..." -ForegroundColor Cyan

# 1. Limpiar carpetas temporales de usuarios
Write-Host "Limpiando archivos temporales de usuarios..." -ForegroundColor Yellow
$users = Get-ChildItem "C:\\Users" -Directory -ErrorAction SilentlyContinue
foreach ($user in $users) {
    $tempPath = "C:\\Users\\$($user.Name)\\AppData\\Local\\Temp"
    if (Test-Path $tempPath) {
        Remove-Item "$tempPath\\*" -Force -Recurse -ErrorAction SilentlyContinue
    }
}
Write-Host "  Archivos temporales eliminados" -ForegroundColor Green

# 2. Vaciar papelera
Write-Host "Vaciando papelera de reciclaje..." -ForegroundColor Yellow
Clear-RecycleBin -Force -ErrorAction SilentlyContinue
Write-Host "  Papelera vaciada" -ForegroundColor Green

# 3. Liberar memoria
Write-Host "Liberando memoria cache..." -ForegroundColor Yellow
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()
Write-Host "  Memoria liberada" -ForegroundColor Green

# 4. Deshabilitar servicios innecesarios
Write-Host "Optimizando servicios..." -ForegroundColor Yellow
$servicesToDisable = @("SysMain", "DiagTrack")
foreach ($service in $servicesToDisable) {
    $svc = Get-Service -Name $service -ErrorAction SilentlyContinue
    if ($svc) {
        Stop-Service -Name $service -Force -ErrorAction SilentlyContinue
        Set-Service -Name $service -StartupType Disabled -ErrorAction SilentlyContinue
        Write-Host "  Servicio $service deshabilitado" -ForegroundColor Green
    }
}

# 5. Limpiar cache del sistema
Write-Host "Limpiando cache del sistema..." -ForegroundColor Yellow
Remove-Item "C:\\Windows\\Temp\\*" -Force -Recurse -ErrorAction SilentlyContinue
Remove-Item "C:\\Windows\\Prefetch\\*" -Force -Recurse -ErrorAction SilentlyContinue
Write-Host "  Cache del sistema limpiada" -ForegroundColor Green

# 6. Optimizar disco (solo análisis rápido)
Write-Host "Analizando disco..." -ForegroundColor Yellow
$volume = Get-Volume -DriveLetter C -ErrorAction SilentlyContinue
if ($volume) {
    $fragmentation = $volume.FragmentationPercentage
    if ($fragmentation) {
        Write-Host "  Fragmentacion actual: $fragmentation%" -ForegroundColor Cyan
        if ($fragmentation -gt 10) {
            Write-Host "  Recomendacion: Ejecutar desfragmentacion manualmente" -ForegroundColor Yellow
        } else {
            Write-Host "  El disco no requiere desfragmentacion" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "Optimizacion completada!" -ForegroundColor Green
'''

SCRIPT_SFC_SCANNOW = '''
Write-Host "Ejecutando sfc /scannow (esto puede tomar varios minutos)..." -ForegroundColor Cyan
$sfc = Start-Process -FilePath "sfc.exe" -ArgumentList "/scannow" -NoNewWindow -Wait -PassThru
if ($sfc.ExitCode -eq 0) {
    Write-Host "SFC completado correctamente" -ForegroundColor Green
} else {
    Write-Host "SFC termino con codigo: $($sfc.ExitCode)" -ForegroundColor Yellow
}
'''


def ejecutar(executor: WinRMExecutor, hostname: str, run_sfc: bool = False):
    """
    Ejecuta optimización en el equipo remoto
    
    Args:
        executor: Instancia de WinRMExecutor
        hostname: Nombre del equipo remoto
        run_sfc: Si True, ejecuta sfc /scannow al final
    """
    print(f"\n🔧 Optimizando {hostname}...")
    print()
    
    # Ejecutar script de optimización
    result = executor.run_script_block(hostname, SCRIPT_OPTIMIZAR, timeout=120)
    
    if result:
        print(result)
    else:
        print("❌ Error durante la optimización")
        return
    
    # Preguntar si ejecutar SFC
    if not run_sfc:
        print()
        respuesta = input("¿Ejecutar sfc /scannow? (puede tomar 10-15 min) (S/N): ").strip().upper()
        run_sfc = respuesta == "S"
    
    if run_sfc:
        print()
        print("⏳ Ejecutando sfc /scannow...")
        sfc_result = executor.run_script_block(hostname, SCRIPT_SFC_SCANNOW, timeout=900)  # 15 min timeout
        if sfc_result:
            print(sfc_result)
    
    print()
    input("Presioná ENTER para continuar...")


def main():
    """Función principal para ejecución standalone"""
    from utils.common import clear_screen
    
    clear_screen()
    print("=" * 60)
    print("🔧 OPTIMIZAR EQUIPO")
    print("=" * 60)
    
    hostname = input("\nInventario: ").strip()
    if not hostname:
        print("❌ Debe ingresar un inventario")
        return
    
    executor = WinRMExecutor()
    
    conn = executor.test_connection(hostname)
    if not conn["ready"]:
        print(f"\n❌ No se pudo conectar a {hostname}")
        input("\nPresioná ENTER para salir...")
        return
    
    ejecutar(executor, hostname)


if __name__ == "__main__":
    main()

