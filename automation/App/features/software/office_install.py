"""
Módulo para instalar Office 365
Corresponde a la opción 8 del menú
"""
import sys
import os
import shutil
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)
from utils.remote_executor import RemoteExecutor


# Rutas de recursos Office
OFFICE_SOURCE_PATH = r"\\pc101338\c$\Tools\Office"
SETUP_EXE = os.path.join(OFFICE_SOURCE_PATH, "setup.exe")
CONFIG_XML = os.path.join(OFFICE_SOURCE_PATH, "config.xml")


SCRIPT_CHECK_OFFICE = '''
# Redirigir Write-Host a Write-Output (ejecución silenciosa)
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
$null = $true  # Silenciar definición de función

try {
    $office = Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*" -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -match "Microsoft 365|Office" } |
        Select-Object DisplayName, DisplayVersion

    if ($office) {
        Write-Host "Office ya esta instalado:" -ForegroundColor Green
        $office | Format-Table -AutoSize
        return $true
    } else {
        Write-Host "Office NO esta instalado" -ForegroundColor Yellow
        return $false
    }
} catch {
    Write-Output "❌ ERROR EN POWERSHELL: $($_.Exception.Message)"
    Write-Output "StackTrace: $($_.ScriptStackTrace)"
    return $false
}
'''

SCRIPT_INSTALL_OFFICE = '''
# Redirigir Write-Host a Write-Output (ejecución silenciosa)
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
$null = $true  # Silenciar definición de función

try {
    $setupPath = "C:\\Temp\\setup.exe"
    $configPath = "C:\\Temp\\config.xml"

    if (-not (Test-Path $setupPath)) {
        Write-Host "Error: setup.exe no encontrado en $setupPath" -ForegroundColor Red
        return
    }

    if (-not (Test-Path $configPath)) {
        Write-Host "Error: config.xml no encontrado en $configPath" -ForegroundColor Red
        return
    }

    Write-Host "Iniciando instalacion de Office 365..." -ForegroundColor Yellow
    Write-Host "Esto puede tomar 10-20 minutos..." -ForegroundColor Gray

    $proc = Start-Process -FilePath $setupPath -ArgumentList "/configure `"$configPath`"" -Wait -PassThru

    if ($proc.ExitCode -eq 0) {
        Write-Host "Instalacion completada" -ForegroundColor Green
    } else {
        Write-Host "La instalacion termino con codigo: $($proc.ExitCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Output "❌ ERROR EN POWERSHELL: $($_.Exception.Message)"
    Write-Output "StackTrace: $($_.ScriptStackTrace)"
}
'''


def copiar_recursos_office(hostname: str, verbose: bool = True):
    """
    Copia los archivos de instalación de Office al equipo remoto
    
    Args:
        hostname: Nombre del equipo remoto
        verbose: Si True, muestra mensajes
    
    Returns:
        bool: True si la copia fue exitosa
    """
    destino_remoto = f"\\\\{hostname}\\c$\\Temp"
    
    try:
        # Crear carpeta si no existe
        os.makedirs(destino_remoto, exist_ok=True)
        
        # Copiar setup.exe
        if verbose:
            print("📦 Copiando setup.exe...")
        
        if os.path.exists(SETUP_EXE):
            shutil.copy2(SETUP_EXE, os.path.join(destino_remoto, "setup.exe"))
            if verbose:
                print("   ✅ setup.exe copiado")
        else:
            if verbose:
                print(f"   ❌ No se encontró: {SETUP_EXE}")
            return False
        
        # Copiar config.xml
        if verbose:
            print("📦 Copiando config.xml...")
        
        if os.path.exists(CONFIG_XML):
            shutil.copy2(CONFIG_XML, os.path.join(destino_remoto, "config.xml"))
            if verbose:
                print("   ✅ config.xml copiado")
        else:
            if verbose:
                print(f"   ❌ No se encontró: {CONFIG_XML}")
            return False
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"❌ Error copiando recursos: {e}")
        return False


def ejecutar(executor: RemoteExecutor, hostname: str):
    """
    Instala Office 365 en el equipo remoto
    
    Args:
        executor: Instancia de RemoteExecutor
        hostname: Nombre del equipo remoto
    """
    print(f"\n📦 Instalación de Office 365 en {hostname}")
    print()
    
    # Verificar si ya está instalado
    print("🔍 Verificando si Office ya está instalado...")
    check_result = executor.run_script_block(hostname, SCRIPT_CHECK_OFFICE, timeout=30)
    
    if check_result:
        print(check_result)
        
        if "ya esta instalado" in check_result:
            continuar = input("\n¿Reinstalar de todos modos? (S/N): ").strip().upper()
            if continuar != "S":
                input("\nPresioná ENTER para continuar...")
                return
    
    # Copiar recursos
    print("\n📂 Copiando archivos de instalación...")
    if not copiar_recursos_office(hostname):
        print("❌ Error copiando archivos de Office")
        input("\nPresioná ENTER para continuar...")
        return
    
    # Instalar Office
    print("\n📥 Instalando Office 365...")
    print("   (Esto puede tomar 10-20 minutos)")
    print()
    
    result = executor.run_script_block(hostname, SCRIPT_INSTALL_OFFICE, timeout=1800)  # 30 min
    
    if result:
        print(result)
    
    # Verificar instalación
    print("\n🔍 Verificando instalación...")
    time.sleep(10)
    
    verify_result = executor.run_script_block(hostname, SCRIPT_CHECK_OFFICE, timeout=30)
    if verify_result:
        print(verify_result)
    
    print()
    input("Presioná ENTER para continuar...")


def main():
    """Función principal para ejecución standalone"""
    from utils.common import clear_screen
    
    clear_screen()
    print("=" * 60)
    print("📦 INSTALAR OFFICE 365")
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

