# ============================================================================
# SCRIPT POWERSHELL: DESINSTALAR SOFTWARE (Versión Manual)
# ============================================================================
# Este script hace lo mismo que el playbook de Ansible pero se ejecuta
# directamente en PowerShell sin necesidad de Ansible
#
# USO:
#   1. Abrir PowerShell como Administrador
#   2. Ejecutar: .\desistalar_manual.ps1
#   3. Ingresar el nombre del software cuando te lo pida
#
# EJEMPLO PARA DELL COMMAND:
#   - Nombre: "Dell Command"
#   - Publisher: "Dell Inc." (opcional, presionar Enter para omitir)
# ============================================================================

# Solicitar información al usuario
Write-Host "`n=== DESINSTALADOR DE SOFTWARE ===" -ForegroundColor Cyan
$searchName = Read-Host "Ingresá el nombre del software a desinstalar (ej: 'Dell Command' o 'Chrome')"
$searchPublisher = Read-Host "Ingresá el Publisher (opcional, presionar Enter para omitir)"

# Si no ingresó publisher, usar cadena vacía
if ([string]::IsNullOrWhiteSpace($searchPublisher)) {
    $searchPublisher = ""
}

Write-Host "`nBuscando software..." -ForegroundColor Yellow

# ============================================================================
# TAREA 1: Buscar software instalado
# ============================================================================
$apps = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
    Where-Object { 
        ($_.DisplayName -like "*$searchName*") -and
        (($searchPublisher -eq "") -or ($_.Publisher -like "*$searchPublisher*"))
    } | 
    Select-Object DisplayName, DisplayVersion, Publisher, UninstallString, PSChildName

if (-not $apps) {
    Write-Host "`n❌ No se encontró software que coincida con '$searchName'" -ForegroundColor Red
    exit 1
}

# Mostrar software encontrado
Write-Host "`n=== Software encontrado ===" -ForegroundColor Green
$apps | Format-Table -AutoSize

# Confirmar antes de desinstalar
$confirm = Read-Host "`n¿Deseás desinstalar estas aplicaciones? (S/N)"
if ($confirm -ne "S" -and $confirm -ne "s" -and $confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Operación cancelada." -ForegroundColor Yellow
    exit 0
}

# ============================================================================
# TAREA 2: Detener procesos relacionados
# ============================================================================
Write-Host "`nDeteniendo procesos relacionados..." -ForegroundColor Yellow
$processes = Get-Process | Where-Object { 
    $_.ProcessName -like "*$searchName*" -or
    $_.MainWindowTitle -like "*$searchName*"
}
if ($processes) {
    $processes | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    Write-Host "Procesos detenidos." -ForegroundColor Green
} else {
    Write-Host "No se encontraron procesos ejecutándose." -ForegroundColor Gray
}

# ============================================================================
# TAREA 3: Desinstalar cada aplicación encontrada
# ============================================================================
foreach ($app in $apps) {
    $displayName = $app.DisplayName
    $uninstallString = $app.UninstallString
    $productCode = $app.PSChildName
    
    Write-Host "`n=== Desinstalando: $displayName ===" -ForegroundColor Cyan
    
    $desinstalado = $false
    
    # MÉTODO 1: Desinstalación MSI
    if ($uninstallString -like "*msiexec*" -or $productCode -match '^{[A-F0-9-]+}$') {
        if ($productCode -match '^{[A-F0-9-]+}$') {
            $msiArgs = "/x $productCode /quiet /norestart"
            Write-Host "Ejecutando: msiexec $msiArgs" -ForegroundColor Gray
            try {
                $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
                $desinstalado = $true
            } catch {
                Write-Host "Error al ejecutar msiexec: $_" -ForegroundColor Red
            }
        } else {
            $guid = ($uninstallString -split '/I')[-1].Trim()
            if ($guid -match '^{[A-F0-9-]+}$') {
                $msiArgs = "/x $guid /quiet /norestart"
                Write-Host "Ejecutando: msiexec $msiArgs" -ForegroundColor Gray
                try {
                    $process = Start-Process -FilePath "msiexec.exe" -ArgumentList $msiArgs -Wait -PassThru -NoNewWindow
                    $desinstalado = $true
                } catch {
                    Write-Host "Error al ejecutar msiexec: $_" -ForegroundColor Red
                }
            }
        }
    } 
    # MÉTODO 2: Desinstalación EXE
    else {
        $cleanUninstall = $uninstallString -replace '"', ''
        if ($cleanUninstall -like "*.exe*") {
            $exePath = ($cleanUninstall -split '\.exe')[0] + '.exe'
            $args = ($cleanUninstall -split '\.exe')[1]
            if ($args) {
                $args = $args.Trim() + " /S /silent /quiet"
            } else {
                $args = "/S /silent /quiet"
            }
            Write-Host "Ejecutando: $exePath $args" -ForegroundColor Gray
            try {
                if (Test-Path $exePath) {
                    $process = Start-Process -FilePath $exePath -ArgumentList $args -Wait -PassThru -NoNewWindow
                    $desinstalado = $true
                } else {
                    Write-Host "⚠️ No se encontró el archivo: $exePath" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "Error al ejecutar desinstalador: $_" -ForegroundColor Red
            }
        }
    }
    
    # Esperar y verificar
    Start-Sleep -Seconds 5
    
    $stillInstalled = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
        Where-Object { $_.DisplayName -eq $displayName }
    
    if (-not $stillInstalled) {
        Write-Host "✅ $displayName desinstalado correctamente" -ForegroundColor Green
    } else {
        Write-Host "⚠️ $displayName aún está instalado (puede requerir reinicio)" -ForegroundColor Yellow
    }
}

# ============================================================================
# TAREA 4: Verificación final
# ============================================================================
Write-Host "`n=== Verificación Final ===" -ForegroundColor Cyan
Start-Sleep -Seconds 3

$stillInstalled = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
    Where-Object { $_.DisplayName -like "*$searchName*" }

if ($stillInstalled) {
    Write-Host "`n⚠️ Software aún instalado:" -ForegroundColor Yellow
    $stillInstalled | Select-Object DisplayName, DisplayVersion | Format-Table -AutoSize
} else {
    Write-Host "`n✅ Software desinstalado correctamente" -ForegroundColor Green
}

Write-Host "`nPresioná cualquier tecla para salir..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

