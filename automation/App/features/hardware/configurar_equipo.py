import os


# ===== RECURSOS =====
DELL_COMMAND_SOURCE = r"\\pc101338\c$\Tools\Dell-Command-Update-Application_6VFWW_WIN_5.4.0_A00.EXE"
NOSLEEP_SOURCE = r"\\pc101338\c$\Tools\NoSleep.exe"
OFFICE_SOURCE_PATH = r"\\pc101338\c$\Tools\Office"
SETUP_EXE = os.path.join(OFFICE_SOURCE_PATH, "setup.exe")
CONFIG_XML = os.path.join(OFFICE_SOURCE_PATH, "config.xml")


# ===== SCRIPTS POWERSHELL =====

SCRIPT_SUSPEND_BITLOCKER = '''
# Redirigir Write-Host a Write-Output (ejecución silenciosa)
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
$null = $true  # Silenciar definición de función

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
# Redirigir Write-Host a Write-Output (ejecución silenciosa)
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
$null = $true  # Silenciar definición de función

try {
    $folder = "C:\\TEMP"
    if (!(Test-Path $folder)) {
        New-Item -Path $folder -ItemType Directory -Force | Out-Null
        Write-Host "Carpeta TEMP creada" -ForegroundColor Green
    } else {
        Write-Host "Carpeta TEMP existe" -ForegroundColor Gray
    }
} catch {
    Write-Output "❌ ERROR EN POWERSHELL: $($_.Exception.Message)"
}
'''

SCRIPT_RUN_NOSLEEP = '''
# Redirigir Write-Host a Write-Output (ejecución silenciosa)
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
$null = $true  # Silenciar definición de función

try {
    $nosleep = "C:\\temp\\NoSleep.exe"
    if (Test-Path $nosleep) {
        Start-Process -FilePath $nosleep -WindowStyle Minimized
        Write-Host "NoSleep iniciado" -ForegroundColor Green
    } else {
        Write-Host "NoSleep.exe no encontrado" -ForegroundColor Yellow
    }
} catch {
    Write-Output "❌ ERROR EN POWERSHELL: $($_.Exception.Message)"
}
'''

SCRIPT_DELL_COMMAND = '''
# Redirigir Write-Host a Write-Output (ejecución silenciosa)
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
$null = $true  # Silenciar definición de función

try {
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
Write-Host "--- Resultado ---" -ForegroundColor Cyan
if (Test-Path $logOut) { Get-Content $logOut | Select-Object -Last 10 }
} catch {
    Write-Output "❌ ERROR EN POWERSHELL: $($_.Exception.Message)"
    Write-Output "StackTrace: $($_.ScriptStackTrace)"
}
'''

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
        Write-Host "Error: setup.exe no encontrado" -ForegroundColor Red
        return
    }

    Write-Host "Instalando Office 365..." -ForegroundColor Yellow

    $proc = Start-Process -FilePath $setupPath -ArgumentList "/configure `"$configPath`"" -Wait -PassThru

    if ($proc.ExitCode -eq 0) {
        Write-Host "Instalacion completada" -ForegroundColor Green
    } else {
        Write-Host "Codigo de salida: $($proc.ExitCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Output "❌ ERROR EN POWERSHELL: $($_.Exception.Message)"
    Write-Output "StackTrace: $($_.ScriptStackTrace)"
}
'''

SCRIPT_ACTIVAR_WINDOWS = '''
# Redirigir Write-Host a Write-Output (ejecución silenciosa)
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
$null = $true  # Silenciar definición de función

try {
    Write-Host "Activando Windows..." -ForegroundColor Yellow

    $keys = @(
        "P9BHN-HYVGH-DVK3V-JHPJ6-HFR9M",
        "3BRT8-N267D-TXT8G-W2F7F-JHW4K",
        "22JFY-NPQ9G-RQ6P2-9PYM7-2R6FT"
    )

    $activated = $false

    foreach ($key in $keys) {
        $result = cscript //nologo C:\\Windows\\System32\\slmgr.vbs /ipk $key 2>&1
        if ($result -match "correctamente|successfully") {
            Write-Host "Clave instalada" -ForegroundColor Green
            $activated = $true
            break
        }
    }

    if ($activated) {
        cscript //nologo C:\\Windows\\System32\\slmgr.vbs /ato 2>&1 | Out-Null
        Write-Host "Activacion completada" -ForegroundColor Green
    }
} catch {
    Write-Output "❌ ERROR EN POWERSHELL: $($_.Exception.Message)"
    Write-Output "StackTrace: $($_.ScriptStackTrace)"
}
'''

SCRIPT_SFC_SCANNOW = '''
# Redirigir Write-Host a Write-Output (ejecución silenciosa)
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
$null = $true  # Silenciar definición de función

try {
    Write-Host "Ejecutando sfc /scannow..." -ForegroundColor Cyan
    $sfc = Start-Process -FilePath "sfc.exe" -ArgumentList "/scannow" -NoNewWindow -Wait -PassThru
    if ($sfc.ExitCode -eq 0) {
        Write-Host "SFC completado correctamente" -ForegroundColor Green
    } else {
        Write-Host "SFC termino con codigo: $($sfc.ExitCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Output "❌ ERROR EN POWERSHELL: $($_.Exception.Message)"
    Write-Output "StackTrace: $($_.ScriptStackTrace)"
}
'''


# ===== FUNCIONES AUXILIARES =====

def copiar_recursos(hostname: str, verbose: bool = True):
    """Copia Dell Command y NoSleep al equipo remoto"""
    destino_remoto = f"\\\\{hostname}\\c$\\temp"
    
    try:
        os.makedirs(destino_remoto, exist_ok=True)
        
        if verbose:
            print("📦 Copiando Dell Command...")
        if os.path.exists(DELL_COMMAND_SOURCE):
            shutil.copy2(DELL_COMMAND_SOURCE, os.path.join(destino_remoto, os.path.basename(DELL_COMMAND_SOURCE)))
            if verbose:
                print("   ✅ Dell Command copiado")
        
        if verbose:
            print("📦 Copiando NoSleep.exe...")
        if os.path.exists(NOSLEEP_SOURCE):
            shutil.copy2(NOSLEEP_SOURCE, os.path.join(destino_remoto, "NoSleep.exe"))
            if verbose:
                print("   ✅ NoSleep copiado")
        
        return True
    except Exception as e:
        if verbose:
            print(f"❌ Error copiando recursos: {e}")
        return False


def copiar_recursos_office(hostname: str, verbose: bool = True):
    """Copia archivos de Office al equipo remoto"""
    destino_remoto = f"\\\\{hostname}\\c$\\Temp"
    
    try:
        os.makedirs(destino_remoto, exist_ok=True)
        
        if verbose:
            print("📦 Copiando setup.exe...")
        if os.path.exists(SETUP_EXE):
            shutil.copy2(SETUP_EXE, os.path.join(destino_remoto, "setup.exe"))
            if verbose:
                print("   ✅ setup.exe copiado")
        
        if verbose:
            print("📦 Copiando config.xml...")
        if os.path.exists(CONFIG_XML):
            shutil.copy2(CONFIG_XML, os.path.join(destino_remoto, "config.xml"))
            if verbose:
                print("   ✅ config.xml copiado")
        
        return True
    except Exception as e:
        if verbose:
            print(f"❌ Error copiando Office: {e}")
        return False


# ===== FUNCIÓN PRINCIPAL =====

def ejecutar(executor: RemoteExecutor, hostname: str):
    """
    Ejecuta la configuración completa del equipo
    
    Args:
        executor: Instancia de RemoteExecutor
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
        lines = result.strip().split('\n')
        for line in lines[-10:]:
            print(f"   {line}")
    
    # PASO 6: Office 365
    print()
    print("=" * 50)
    print("📦 PASO 5/7: Office 365...")
    
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
    
    executor = RemoteExecutor()
    
    conn = executor.test_connection(hostname)
    if not conn["ready"]:
        print(f"\n❌ No se pudo conectar a {hostname}")
        input("\nPresioná ENTER para salir...")
        return
    
    ejecutar(executor, hostname)


if __name__ == "__main__":
    main()
