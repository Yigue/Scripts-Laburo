"""
Módulo para reiniciar equipos remotos
Corresponde a la opción 4 del menú
"""
import sys
import os
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)
from utils.remote_executor import RemoteExecutor


SCRIPT_SUSPEND_BITLOCKER = '''
# Suspender BitLocker en C: por 1 reinicio
try {
    $bl = Get-BitLockerVolume -MountPoint "C:" -ErrorAction SilentlyContinue
    if ($bl -and $bl.ProtectionStatus -eq "On") {
        Suspend-BitLocker -MountPoint "C:" -RebootCount 1 -ErrorAction Stop
        Write-Host "BitLocker suspendido por 1 reinicio" -ForegroundColor Green
    } else {
        Write-Host "BitLocker no esta activo o ya esta suspendido" -ForegroundColor Yellow
    }
} catch {
    Write-Host "No se pudo suspender BitLocker: $_" -ForegroundColor Yellow
}

Get-BitLockerVolume -ErrorAction SilentlyContinue | Format-Table MountPoint, ProtectionStatus, VolumeStatus
'''


def ejecutar(executor: RemoteExecutor, hostname: str, wait_for_restart: bool = True):
    """
    Reinicia el equipo remoto
    
    Args:
        executor: Instancia de RemoteExecutor
        hostname: Nombre del equipo remoto
        wait_for_restart: Si True, espera a que el equipo vuelva a estar online
    """
    print(f"\n🔄 Preparando reinicio de {hostname}...")
    
    # Si es notebook, suspender BitLocker
    if hostname.upper().startswith('N'):
        print("\n📀 Suspendiendo BitLocker...")
        bl_result = executor.run_script_block(hostname, SCRIPT_SUSPEND_BITLOCKER, timeout=30)
        if bl_result:
            print(bl_result)
    
    # Confirmar reinicio
    print()
    confirmar = input(f"¿Confirmar reinicio de {hostname}? (S/N): ").strip().upper()
    if confirmar != "S":
        print("Reinicio cancelado")
        input("\nPresioná ENTER para continuar...")
        return
    
    # Reiniciar
    print(f"\n🔄 Reiniciando {hostname}...")
    
    success = executor.restart_computer(hostname, force=True, wait=False)
    
    if not success:
        print(f"❌ Error al enviar comando de reinicio")
        input("\nPresioná ENTER para continuar...")
        return
    
    if wait_for_restart:
        print(f"\n⏳ Esperando a que {hostname} vuelva a estar online...")
        
        # Esperar a que se apague
        time.sleep(15)
        
        # Esperar a que vuelva (máximo 10 minutos)
        for i in range(60):
            time.sleep(10)
            print(f"   Intento {i+1}/60...")
            
            if executor.test_ping(hostname, count=1, timeout=3):
                # Esperar un poco más para WinRM
                time.sleep(20)
                
                conn = executor.test_connection(hostname, verbose=False)
                if conn["ready"]:
                    print(f"\n✅ {hostname} está online nuevamente")
                    input("\nPresioná ENTER para continuar...")
                    return
        
        print(f"\n⚠ Timeout esperando que {hostname} vuelva a estar online")
    else:
        print(f"\n✅ Comando de reinicio enviado a {hostname}")
    
    input("\nPresioná ENTER para continuar...")


def main():
    """Función principal para ejecución standalone"""
    from utils.common import clear_screen
    
    clear_screen()
    print("=" * 60)
    print("🔄 REINICIAR EQUIPO")
    print("=" * 60)
    
    hostname = input("\nInventario: ").strip()
    if not hostname:
        print("❌ Debe ingresar un inventario")
        return
    
    executor = RemoteExecutor()
    
    conn = executor.test_connection(hostname)
    if not conn["ready"]:
        print(f"\n❌ No se pudo conectar a {hostname}")
        input("\nPresioná ENTER para salir...")
        return
    
    ejecutar(executor, hostname)


if __name__ == "__main__":
    main()

