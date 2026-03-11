param(
    [Parameter(Mandatory=$true)][string]$DeviceName,
    [Parameter(Mandatory=$true)][string]$SiteCode,
    [Parameter(Mandatory=$true)][string]$SccmServer
)

$ErrorActionPreference = "Stop"

try {
    # 1. Buscar el módulo ConfigurationManager
    # Intenta buscar en la ruta estándar de la consola
    if ($env:SMS_ADMIN_UI_PATH) {
        $psd1 = Join-Path $env:SMS_ADMIN_UI_PATH "..\ConfigurationManager.psd1"
    } else {
        # Fallback para búsquedas comunes si la variable de entorno no está (poco probable si la consola está instalada)
        $psd1 = "C:\Program Files (x86)\Microsoft Configuration Manager\AdminConsole\bin\ConfigurationManager.psd1"
    }

    if (-not (Test-Path $psd1)) {
        Write-Output "ERROR_JSON: { ""error"": ""No se encontró ConfigurationManager.psd1. La consola SCCM no parece estar instalada."" }"
        exit 1
    }

    # 2. Importar el módulo
    Import-Module $psd1 -Force -ErrorAction Stop

    # 3. Gestionar el PSDrive (Evitar errores de "Drive not found")
    $driveName = $SiteCode
    $drive = Get-PSDrive -PSProvider CMSite -Name $driveName -ErrorAction SilentlyContinue
    
    if (-not $drive) {

                # Intentamos crearlo apuntando al Root server
        New-PSDrive -Name $driveName -PSProvider CMSite -Root $SccmServer -Description "SCCM Drive" -ErrorAction Stop | Out-Null
    }

    # 4. Cambiar al contexto del sitio
    Set-Location "${driveName}:"

    # 5. Consultar el dispositivo
    $device = Get-CMDevice -Name $DeviceName -ErrorAction SilentlyContinue |
        Select-Object Name, ResourceId, IsClient, ClientType, LastActiveTime, 
                      LastLogonUserName, OperatingSystemNameAndVersion, 
                      PrimaryUser, ADSiteName, IsActive, ClientVersion

    # 6. Salida de resultados
    if (-not $device) {
        # Devolver un JSON indicando que no se encontró
        $result = @{
            found = $false
            message = "Dispositivo '$DeviceName' no encontrado en el sitio $SiteCode"
        }
    } else {
        $result = @{
            found = $true
            data = $device
        }
    }

    # Convertir a JSON para que Ansible lo parsee fácilmente
    $result | ConvertTo-Json -Depth 4

} catch {
    # Captura de errores fatales
    $errorMsg = $_.Exception.Message
    $errResult = @{
        found = $false
        error = "EXCEPCION: $errorMsg"
    }
    $errResult | ConvertTo-Json -Depth 2
} finally {
    # Limpieza: Volver a C: para liberar el handle del proveedor si fuera necesario
    Set-Location C:\ -ErrorAction SilentlyContinue
}
