"""
Módulo para instalar y actualizar Dell Command Update
Corresponde a la opción 5 del menú
"""
import sys
import os
import shutil

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)
from utils.remote_executor import RemoteExecutor


# Rutas de recursos
DELL_COMMAND_SOURCE = r"\\pc101338\c$\iTools\Dell-Command-Update-Application_6VFWW_WIN_5.4.0_A00.EXE"
NOSLEEP_SOURCE = r"\\pc101338\c$\iTools\NoSleep.exe"


SCRIPT_DELL_COMMAND = '''
Write-Host "Validando si Dell Command esta instalado..." -ForegroundColor Yellow

$dellCommandInstalled = Get-ItemProperty -Path `
    'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*', `
    'HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*' `
    -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -like "*Dell Command*Update*" }

if ($dellCommandInstalled) {
    Write-Host "Dell Command ya esta instalado." -ForegroundColor Green
    Write-Host "Version: $($dellCommandInstalled.DisplayVersion)"
} else {
    Write-Host "Dell Command no esta instalado. Instalando..." -ForegroundColor Yellow
    
    $installer = "C:\\TEMP\\Dell-Command-Update-Application_6VFWW_WIN_5.4.0_A00.EXE"
    
    if (Test-Path $installer) {
        $proc = Start-Process -FilePath $installer -ArgumentList "/s" -Wait -PassThru
        
        if ($proc.ExitCode -ne 0) {
            Write-Host "Instalacion fallida con codigo $($proc.ExitCode)" -ForegroundColor Red
            return
        } else {
            Write-Host "Instalacion completada exitosamente." -ForegroundColor Green
        }
    } else {
        Write-Host "Instalador no encontrado en $installer" -ForegroundColor Red
        return
    }
}

# Buscar dcu-cli
$DCUPath = if (Test-Path "C:\\Program Files (x86)\\Dell\\CommandUpdate\\dcu-cli.exe") {
    "C:\\Program Files (x86)\\Dell\\CommandUpdate\\dcu-cli.exe"
} elseif (Test-Path "C:\\Program Files\\Dell\\CommandUpdate\\dcu-cli.exe") {
    "C:\\Program Files\\Dell\\CommandUpdate\\dcu-cli.exe"
} else {
    $null
}

if (-not $DCUPath) {
    Write-Host "Dell Command Update CLI no encontrado." -ForegroundColor Red
    return
}

Write-Host ""
Write-Host "Ejecutando actualizaciones..." -ForegroundColor Yellow
Write-Host "Esto puede tomar varios minutos..."
Write-Host ""

$logOut = "C:\\TEMP\\dcu-output.txt"
$logErr = "C:\\TEMP\\dcu-error.txt"

Start-Process -FilePath $DCUPath `
    -ArgumentList "/applyUpdates" `
    -WindowStyle Hidden `
    -RedirectStandardOutput $logOut `
    -RedirectStandardError $logErr `
    -Wait

Write-Host "Actualizacion finalizada." -ForegroundColor Green
Write-Host ""
Write-Host "--- Resultado de actualizaciones ---" -ForegroundColor Cyan
if (Test-Path $logOut) { Get-Content $logOut }
Write-Host ""
Write-Host "--- Errores (si hubo) ---" -ForegroundColor Magenta
if (Test-Path $logErr) { Get-Content $logErr }
'''

SCRIPT_RUN_NOSLEEP = '''
$nosleep = "C:\\temp\\NoSleep.exe"
if (Test-Path $nosleep) {
    Start-Process -FilePath $nosleep -WindowStyle Minimized
    Write-Host "NoSleep iniciado" -ForegroundColor Green
} else {
    Write-Host "NoSleep.exe no encontrado" -ForegroundColor Yellow
}
'''


def copiar_recursos(hostname: str, verbose: bool = True):
    """
    Copia los recursos necesarios al equipo remoto
    
    Args:
        hostname: Nombre del equipo remoto
        verbose: Si True, muestra mensajes
    
    Returns:
        bool: True si la copia fue exitosa
    """
    destino_remoto = f"\\\\{hostname}\\c$\\temp"
    
    try:
        # Crear carpeta si no existe
        os.makedirs(destino_remoto, exist_ok=True)
        
        # Copiar Dell Command
        if verbose:
            print("📦 Copiando instalador Dell Command...")
        
        if os.path.exists(DELL_COMMAND_SOURCE):
            dest_file = os.path.join(destino_remoto, os.path.basename(DELL_COMMAND_SOURCE))
            shutil.copy2(DELL_COMMAND_SOURCE, dest_file)
            if verbose:
                print("   ✅ Dell Command copiado")
        else:
            if verbose:
                print(f"   ⚠ No se encontró: {DELL_COMMAND_SOURCE}")
        
        # Copiar NoSleep
        if verbose:
            print("📦 Copiando NoSleep.exe...")
        
        if os.path.exists(NOSLEEP_SOURCE):
            dest_file = os.path.join(destino_remoto, "NoSleep.exe")
            shutil.copy2(NOSLEEP_SOURCE, dest_file)
            if verbose:
                print("   ✅ NoSleep copiado")
        else:
            if verbose:
                print(f"   ⚠ No se encontró: {NOSLEEP_SOURCE}")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"❌ Error copiando recursos: {e}")
        return False


def ejecutar(executor: RemoteExecutor, hostname: str, copiar: bool = True):
    """
    Instala/actualiza Dell Command Update en el equipo remoto
    
    Args:
        executor: Instancia de RemoteExecutor
        hostname: Nombre del equipo remoto
        copiar: Si True, copia los recursos primero
    """
    print(f"\n🔧 Dell Command Update para {hostname}")
    print()
    
    # Copiar recursos
    if copiar:
        if not copiar_recursos(hostname):
            print("❌ Error copiando recursos")
            input("\nPresioná ENTER para continuar...")
            return
    
    # Ejecutar NoSleep para evitar que el equipo entre en suspensión
    print("\n💤 Iniciando NoSleep...")
    executor.run_script_block(hostname, SCRIPT_RUN_NOSLEEP, timeout=10, verbose=False)
    
    # Ejecutar Dell Command
    print("\n📥 Ejecutando Dell Command Update...")
    print("   (Esto puede tomar 10-30 minutos)")
    print()
    
    result = executor.run_script_block(hostname, SCRIPT_DELL_COMMAND, timeout=1800)  # 30 min timeout
    
    if result:
        print(result)
    else:
        print("❌ Error ejecutando Dell Command Update")
    
    print()
    input("Presioná ENTER para continuar...")


def main():
    """Función principal para ejecución standalone"""
    from utils.common import clear_screen
    
    clear_screen()
    print("=" * 60)
    print("🔧 DELL COMMAND UPDATE")
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

