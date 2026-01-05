# Lista todas las aplicaciones instaladas en el sistema
# Lee del registro de Windows y exporta lista a C:\TEMP\apps_list.xml

try {
    function Get-InstalledApplications {
        param ([string]$RegistryPath)
        
        Get-ItemProperty -Path $RegistryPath -ErrorAction SilentlyContinue | ForEach-Object {
            $_ | Select-Object @{
                Name       = 'Name'
                Expression = { $_.DisplayName }
            }, @{
                Name       = 'Version'
                Expression = { $_.DisplayVersion }
            }, @{
                Name       = 'Publisher'
                Expression = { $_.Publisher }
            }, @{
                Name       = 'UninstallString'
                Expression = { $_.UninstallString }
            }
        } | Where-Object { $_.Name -ne $null }
    }

    $RegistryPaths = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )

    # Obtener todas las apps
    $Applications = foreach ($Path in $RegistryPaths) {
        Get-InstalledApplications -RegistryPath $Path
    }

    # Ordenar y numerar
    $Applications = $Applications | Sort-Object Name | Select-Object -Unique Name, Version, Publisher, UninstallString

    $index = 0
    $output = @()
    foreach ($app in $Applications) {
        $output += [PSCustomObject]@{
            Index = $index
            Name = $app.Name
            Version = $app.Version
            Publisher = $app.Publisher
        }
        $index++
    }

    $output | Format-Table Index, Name, Version, Publisher -AutoSize

    # Crear directorio si no existe
    if (!(Test-Path "C:\TEMP")) {
        New-Item -Path "C:\TEMP" -ItemType Directory -Force | Out-Null
    }

    # Guardar para referencia
    $Applications | Export-Clixml -Path "C:\TEMP\apps_list.xml" -Force

    Write-Output ""
    Write-Output "✅ Total: $($Applications.Count) aplicaciones"
} catch {
    Write-Output "❌ ERROR: $($_.Exception.Message)"
    Write-Output "StackTrace: $($_.ScriptStackTrace)"
    throw
}

