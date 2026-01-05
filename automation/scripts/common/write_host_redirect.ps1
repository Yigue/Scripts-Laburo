# Redirigir Write-Host a Write-Output para compatibilidad con pypsrp
# Este script debe incluirse al inicio de todos los scripts PowerShell remotos
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
$null = $true  # Silenciar salida de la definición de función

