"""
Módulo para configuración completa de equipos
Corresponde a la opción 2 del menú
Ejecuta: Dell Command, Office, Licencia Windows, SFC
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.winrm_executor import WinRMExecutor

# Importar módulos individuales
from remote.dell_command import copiar_recursos, SCRIPT_DELL_COMMAND, SCRIPT_RUN_NOSLEEP
from remote.office_install import copiar_recursos_office, SCRIPT_INSTALL_OFFICE, SCRIPT_CHECK_OFFICE
from remote.activar_windows import SCRIPT_ACTIVAR_WINDOWS
from remote.optimizar import SCRIPT_SFC_SCANNOW


SCRIPT_SUSPEND_BITLOCKER = '''
try {
    $bl = Get-BitLockerVolume -MountPoint "C:" -ErrorAction SilentlyContinue
    if ($bl -and $bl.ProtectionStatus -eq "On") {
        Suspend-BitLocker -MountPoint "C:" -RebootCount 1 -ErrorAction Stop
        Write-Host "BitLocker suspendido por 1 reinicio" -ForegroundColor Green
    }
} catch {
    Write-Host "BitLocker no requiere suspension" -ForegroundColor Gray
}
'''

SCRIPT_CREATE_TEMP = '''
$folder = "C:\\TEMP"
if (!(Test-Path $folder)) {
    New-Item -Path $folder -ItemType Directory -Force | Out-Null
    Write-Host "Carpeta TEMP creada" -ForegroundColor Green
} else {
    Write-Host "Carpeta TEMP existe" -ForegroundColor Gray
}
'''


def ejecutar(executor: WinRMExecutor, hostname: str):
    """
    Ejecuta la configuración completa del equipo
    
    Args:
        executor: Instancia de WinRMExecutor
        hostname: Nombre del equipo remoto
    """
    print(f"\n🔧 CONFIGURACIÓN COMPLETA DE {hostname}")
    print("=" * 50)
    print()
    print("Este proceso incluye:")
    print("  1. Copiar recursos")
    print("  2. Suspender BitLocker (si aplica)")
    print("  3. Instalar/actualizar Dell Command")
    print("  4. Instalar Office 365")
    print("  5. Activar licencia Windows")
    print("  6. Ejecutar SFC /scannow")
    print("  7. Reiniciar equipo")
    print()
    print("⏱️ Tiempo estimado: 30-60 minutos")
    print()
    
    confirmar = input("¿Continuar? (S/N): ").strip().upper()
    if confirmar != "S":
        print("Operación cancelada")
        input("\nPresioná ENTER para continuar...")
        return
    
    print()
    start_time = time.time()
    
    # PASO 1: Crear carpeta TEMP
    print("=" * 50)
    print("📁 PASO 1/7: Preparando carpeta TEMP...")
    executor.run_script_block(hostname, SCRIPT_CREATE_TEMP, timeout=10, verbose=False)
    
    # PASO 2: Copiar recursos
    print("=" * 50)
    print("📦 PASO 2/7: Copiando recursos...")
    copiar_recursos(hostname, verbose=True)
    copiar_recursos_office(hostname, verbose=True)
    
    # PASO 3: Ejecutar NoSleep
    print()
    print("💤 Iniciando NoSleep...")
    executor.run_script_block(hostname, SCRIPT_RUN_NOSLEEP, timeout=10, verbose=False)
    
    # PASO 4: Suspender BitLocker (si es notebook)
    if hostname.upper().startswith('N'):
        print("=" * 50)
        print("🔐 PASO 3/7: Suspendiendo BitLocker...")
        result = executor.run_script_block(hostname, SCRIPT_SUSPEND_BITLOCKER, timeout=30)
        if result:
            print(result)
    else:
        print("=" * 50)
        print("🔐 PASO 3/7: BitLocker (no aplica para PC)")
    
    # PASO 5: Dell Command Update
    print("=" * 50)
    print("🔧 PASO 4/7: Dell Command Update...")
    print("   (Esto puede tomar 10-30 minutos)")
    result = executor.run_script_block(hostname, SCRIPT_DELL_COMMAND, timeout=1800)
    if result:
        # Solo mostrar últimas líneas
        lines = result.strip().split('\n')
        for line in lines[-15:]:
            print(f"   {line}")
    
    # PASO 6: Office 365
    print()
    print("=" * 50)
    print("📦 PASO 5/7: Office 365...")
    
    # Verificar si ya está instalado
    check_result = executor.run_script_block(hostname, SCRIPT_CHECK_OFFICE, timeout=30)
    
    if check_result and "ya esta instalado" in check_result:
        print("   Office ya está instalado, saltando...")
    else:
        print("   Instalando Office 365...")
        print("   (Esto puede tomar 10-20 minutos)")
        result = executor.run_script_block(hostname, SCRIPT_INSTALL_OFFICE, timeout=1800)
        if result:
            print(f"   {result}")
    
    # PASO 7: Activar Windows
    print()
    print("=" * 50)
    print("🔑 PASO 6/7: Activando Windows...")
    result = executor.run_script_block(hostname, SCRIPT_ACTIVAR_WINDOWS, timeout=60)
    if result:
        lines = result.strip().split('\n')
        for line in lines[-5:]:
            print(f"   {line}")
    
    # PASO 8: SFC /scannow
    print()
    print("=" * 50)
    print("🔍 PASO 7/7: Ejecutando SFC /scannow...")
    print("   (Esto puede tomar 10-15 minutos)")
    result = executor.run_script_block(hostname, SCRIPT_SFC_SCANNOW, timeout=900)
    if result:
        print(f"   {result}")
    
    # Calcular tiempo total
    elapsed = time.time() - start_time
    elapsed_min = int(elapsed // 60)
    elapsed_sec = int(elapsed % 60)
    
    print()
    print("=" * 50)
    print(f"✅ CONFIGURACIÓN COMPLETADA")
    print(f"   Tiempo total: {elapsed_min}m {elapsed_sec}s")
    print("=" * 50)
    
    # Preguntar si reiniciar
    print()
    reiniciar = input("¿Reiniciar el equipo ahora? (S/N): ").strip().upper()
    
    if reiniciar == "S":
        print(f"\n🔄 Reiniciando {hostname}...")
        executor.restart_computer(hostname, force=True, wait=False)
        print("   Comando de reinicio enviado")
    
    print()
    input("Presioná ENTER para continuar...")


def main():
    """Función principal para ejecución standalone"""
    from utils.common import clear_screen
    
    clear_screen()
    print("=" * 60)
    print("🔧 CONFIGURACIÓN COMPLETA DE EQUIPO")
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

