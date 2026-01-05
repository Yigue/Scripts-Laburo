# Desinstala una aplicación por su índice
# Parámetro: $AppIndex - Índice de la aplicación en la lista

param(
    [Parameter(Mandatory=$true)]
    [int]$AppIndex
)

try {
    # Importar lista de aplicaciones
    if (!(Test-Path "C:\TEMP\apps_list.xml")) {
        Write-Output "❌ No se encontró lista de aplicaciones"
        Write-Output "   Ejecutar primero 'Listar aplicaciones'"
        throw "Lista de aplicaciones no encontrada"
    }

    $apps = Import-Clixml -Path "C:\TEMP\apps_list.xml"

    if ($AppIndex -lt 0 -or $AppIndex -ge $apps.Count) {
        Write-Output "❌ Índice inválido: $AppIndex"
        Write-Output "   Debe estar entre 0 y $($apps.Count - 1)"
        throw "Índice inválido"
    }

    $app = $apps[$AppIndex]

    if ([string]::IsNullOrWhiteSpace($app.UninstallString)) {
        Write-Output "❌ La aplicación no tiene UninstallString"
        Write-Output "   No se puede desinstalar automáticamente"
        throw "UninstallString no disponible"
    }

    Write-Output "🗑️ Desinstalando: $($app.Name)"
    Write-Output "   Versión: $($app.Version)"
    Write-Output "   Publisher: $($app.Publisher)"
    Write-Output ""

    # Extraer comando y argumentos
    $uninstallString = $app.UninstallString

    # Detectar si es MSI o EXE
    if ($uninstallString -match "msiexec") {
        # Es MSI - agregar /quiet /norestart
        $uninstallString = $uninstallString -replace "/I", "/X"
        
        if ($uninstallString -notmatch "/quiet") {
            $uninstallString += " /quiet /norestart"
        }
        
        Write-Output "   Comando MSI: $uninstallString"
        
        # Ejecutar con cmd
        $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $uninstallString -Wait -PassThru -WindowStyle Hidden
    }
    else {
        # Es EXE - intentar con /S /SILENT /VERYSILENT
        Write-Output "   Comando EXE: $uninstallString"
        
        # Separar exe y argumentos
        if ($uninstallString -match '^"([^"]+)"(.*)$') {
            $exe = $Matches[1]
            $args = $Matches[2].Trim()
        }
        elseif ($uninstallString -match '^([^\s]+)(.*)$') {
            $exe = $Matches[1]
            $args = $Matches[2].Trim()
        }
        else {
            $exe = $uninstallString
            $args = ""
        }
        
        # Agregar flags silenciosos si no existen
        if ($args -notmatch "/(S|SILENT|VERYSILENT|quiet)") {
            $args += " /S /VERYSILENT"
        }
        
        $process = Start-Process -FilePath $exe -ArgumentList $args -Wait -PassThru -WindowStyle Hidden
    }

    if ($process.ExitCode -eq 0 -or $process.ExitCode -eq 3010) {
        Write-Output "✅ Desinstalación completada"
        if ($process.ExitCode -eq 3010) {
            Write-Output "⚠️ Se requiere reinicio del sistema"
        }
    }
    else {
        Write-Output "⚠️ Desinstalación completó con código: $($process.ExitCode)"
    }

} catch {
    Write-Output "❌ ERROR: $($_.Exception.Message)"
    Write-Output "StackTrace: $($_.ScriptStackTrace)"
    throw
}

