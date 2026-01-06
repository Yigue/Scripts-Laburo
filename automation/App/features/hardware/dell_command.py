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
from utils.streaming import run_with_streaming, LogFilePoller


# Rutas de recursos
DELL_COMMAND_SOURCE = r"\\pc101338\c$\Tools\Dell-Command-Update-Application_6VFWW_WIN_5.4.0_A00.EXE"
NOSLEEP_SOURCE = r"\\pc101338\c$\Tools\NoSleep.exe"


# Script de Dell Command Update con logging en tiempo real
SCRIPT_DELL_COMMAND = '''
# Configuración de logging en tiempo real
$global:LogFile = "C:\\TEMP\\dell_command.log"
"" | Set-Content $global:LogFile -Encoding UTF8

function Log {
    param([string]$Message)
    $Message | Add-Content $global:LogFile -Encoding UTF8
    Write-Output $Message
}

try {
Log "Validando si Dell Command esta instalado..."

$dellCommandInstalled = Get-ItemProperty -Path `
    'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*', `
    'HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*' `
    -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -like "*Dell Command*Update*" }

if ($dellCommandInstalled) {
    Log "✅ Dell Command ya esta instalado."
    Log "   Version: $($dellCommandInstalled.DisplayVersion)"
} else {
    Log "Dell Command no esta instalado. Instalando..."
    
    $installer = "C:\\TEMP\\Dell-Command-Update-Application_6VFWW_WIN_5.4.0_A00.EXE"
    
    if (Test-Path $installer) {
        Log "   Ejecutando instalador..."
        $proc = Start-Process -FilePath $installer -ArgumentList "/s" -Wait -PassThru
        
        if ($proc.ExitCode -ne 0) {
            Log "❌ Instalacion fallida con codigo $($proc.ExitCode)"
            return
        } else {
            Log "✅ Instalacion completada exitosamente."
        }
    } else {
        Log "❌ Instalador no encontrado en $installer"
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
    Log "❌ Dell Command Update CLI no encontrado."
    return
}

Log ""
Log "🔍 Buscando actualizaciones disponibles..."

# Primero escanear para ver qué hay disponible
$scanLog = "C:\\TEMP\\dcu-scan.txt"
Start-Process -FilePath $DCUPath `
    -ArgumentList "/scan -outputLog=$scanLog" `
    -WindowStyle Hidden `
    -Wait

# Mostrar updates disponibles
if (Test-Path $scanLog) {
    $scanContent = Get-Content $scanLog -Raw
    if ($scanContent -match "No updates") {
        Log "✅ No hay actualizaciones pendientes."
        return
    }
}

Log ""
Log "📥 Aplicando actualizaciones..."
Log "   (Este proceso puede tomar 10-30 minutos)"
Log ""

# Aplicar updates con logging detallado
$updateLog = "C:\\TEMP\\dcu-update.txt"
$proc = Start-Process -FilePath $DCUPath `
    -ArgumentList "/applyUpdates -autoSuspendBitLocker=enable -outputLog=$updateLog" `
    -WindowStyle Hidden `
    -Wait `
    -PassThru

# Parsear el log de actualización para mostrar qué se actualizó
if (Test-Path $updateLog) {
    $updateContent = Get-Content $updateLog -ErrorAction SilentlyContinue
    foreach ($line in $updateContent) {
        # Filtrar líneas relevantes
        if ($line -match "Installing|Downloading|Updated|Success|Failed|Error|BIOS|Driver") {
            Log "   $line"
        }
    }
}

Log ""
if ($proc.ExitCode -eq 0) {
    Log "✅ Actualizacion completada exitosamente."
} elseif ($proc.ExitCode -eq 1) {
    Log "✅ Actualizaciones aplicadas. Se requiere reinicio."
} elseif ($proc.ExitCode -eq 500) {
    Log "ℹ️ No hay actualizaciones disponibles."
} else {
    Log "⚠️ Proceso terminado con codigo: $($proc.ExitCode)"
}

} catch {
    $errorMsg = "❌ ERROR: $($_.Exception.Message)"
    $errorMsg | Add-Content $global:LogFile -Encoding UTF8
    Write-Output $errorMsg
}
'''

SCRIPT_RUN_NOSLEEP = '''
try {
    $nosleep = "C:\\temp\\NoSleep.exe"
    if (Test-Path $nosleep) {
        Start-Process -FilePath $nosleep -WindowStyle Minimized
        Write-Output "NoSleep iniciado"
    }
} catch {
    Write-Output "Error: $($_.Exception.Message)"
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
    
    # Ejecutar Dell Command con streaming en tiempo real
    print("\n📥 Ejecutando Dell Command Update...")
    print("   (Esto puede tomar 10-30 minutos)")
    print()
    
    # Usar streaming para mostrar progreso en tiempo real
    result = run_with_streaming(
        executor, 
        hostname, 
        SCRIPT_DELL_COMMAND,
        operation_name="Dell Command Update",
        timeout=1800,
        log_filename="dell_command.log"
    )
    
    if not result:
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
