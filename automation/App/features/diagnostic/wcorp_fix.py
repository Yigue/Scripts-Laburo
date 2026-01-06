"""
Módulo para solucionar problemas de conexión WCORP
Corresponde a la opción 6 del menú
"""
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)
from utils.remote_executor import RemoteExecutor


SCRIPT_WCORP_FIX = '''
# Redirigir Write-Host a Write-Output (ejecución silenciosa)
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
$null = $true  # Silenciar definición de función

try {

# 1. Eliminar certificados vencidos
Write-Host "1. Limpiando certificados..." -ForegroundColor Yellow
$store = New-Object System.Security.Cryptography.X509Certificates.X509Store("My", "LocalMachine")
$store.Open("ReadWrite")
$currentDate = (Get-Date).AddDays(7)
$removedCount = 0

foreach ($cert in $store.Certificates) {
    if ($cert.NotAfter -lt $currentDate -or $cert.Issuer -like "*Microsoft Intune MDM Device CA*") {
        $store.Remove($cert)
        $removedCount++
    }
}
$store.Close()
Write-Host "   Certificados eliminados: $removedCount" -ForegroundColor Green

# 2. Limpiar cache DNS
Write-Host ""
Write-Host "2. Limpiando cache DNS..." -ForegroundColor Yellow
Clear-DnsClientCache
Write-Host "   Cache DNS limpiada" -ForegroundColor Green

# 3. Desconectar WiFi actual
Write-Host ""
Write-Host "3. Desconectando WiFi actual..." -ForegroundColor Yellow
netsh wlan disconnect | Out-Null
Write-Host "   Desconectado" -ForegroundColor Green

# 4. Eliminar perfiles WiFi guardados
Write-Host ""
Write-Host "4. Eliminando perfiles WiFi guardados..." -ForegroundColor Yellow
$profiles = netsh wlan show profiles | Select-String "Todos los perfiles de usuario|All User Profile" | ForEach-Object {
    ($_ -split ":")[1].Trim()
} | Where-Object { $_ -ne "" }

foreach ($profile in $profiles) {
    netsh wlan delete profile name="$profile" | Out-Null
    Write-Host "   Eliminado: $profile" -ForegroundColor Gray
}
Write-Host "   Perfiles eliminados" -ForegroundColor Green

# 5. Crear perfil WCORP
Write-Host ""
Write-Host "5. Creando perfil WCORP..." -ForegroundColor Yellow

$xmlPath = "C:\\Windows\\temp\\WCORP.xml"
if (Test-Path $xmlPath) { Remove-Item $xmlPath -Force }

$wcorpXml = @'
<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
<name>WCORP</name>
<SSIDConfig>
<SSID>
<hex>57434F5250</hex>
<name>WCORP</name>
</SSID>
<nonBroadcast>false</nonBroadcast>
</SSIDConfig>
<connectionType>ESS</connectionType>
<connectionMode>auto</connectionMode>
<autoSwitch>false</autoSwitch>
<MSM>
<security>
<authEncryption>
<authentication>WPA2</authentication>
<encryption>AES</encryption>
<useOneX>true</useOneX>
</authEncryption>
<OneX xmlns="http://www.microsoft.com/networking/OneX/v1">
<authMode>machine</authMode>
<EAPConfig><EapHostConfig xmlns="http://www.microsoft.com/provisioning/EapHostConfig">
<EapMethod><Type xmlns="http://www.microsoft.com/provisioning/EapCommon">13</Type>
<VendorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorId>
<VendorType xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorType>
<AuthorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</AuthorId></EapMethod>
<Config xmlns="http://www.microsoft.com/provisioning/EapHostConfig">
<Eap xmlns="http://www.microsoft.com/provisioning/BaseEapConnectionPropertiesV1">
<Type>13</Type>
<EapType xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV1">
<CredentialsSource>
<CertificateStore>
<SimpleCertSelection>true</SimpleCertSelection>
</CertificateStore>
</CredentialsSource>
<ServerValidation>
<DisableUserPromptForServerValidation>false</DisableUserPromptForServerValidation>
<ServerNames></ServerNames>
</ServerValidation>
<DifferentUsername>false</DifferentUsername>
<PerformServerValidation xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV2">false</PerformServerValidation>
<AcceptServerName xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV2">false</AcceptServerName>
</EapType></Eap></Config></EapHostConfig></EAPConfig>
</OneX>
</security>
</MSM>
</WLANProfile>
'@

Set-Content -Path $xmlPath -Value $wcorpXml
netsh wlan add profile filename=$xmlPath user=all | Out-Null
netsh wlan set profileorder name="WCORP" interface="Wi-Fi" priority=1 2>$null
Write-Host "   Perfil WCORP creado" -ForegroundColor Green

# 6. Conectar a WCORP
Write-Host ""
Write-Host "6. Conectando a WCORP..." -ForegroundColor Yellow
netsh wlan connect name="WCORP" | Out-Null

$maxIntentos = 6
$connected = $false

for ($i = 1; $i -le $maxIntentos -and -not $connected; $i++) {
    Start-Sleep -Seconds 10
    $wifiInfo = netsh wlan show interfaces
    $wifiConnected = $wifiInfo | Select-String -Pattern "SSID\\s+: WCORP"
    
    if ($wifiConnected) {
        Write-Host "   Conectado a WCORP" -ForegroundColor Green
        
        # Verificar internet
        $pingResult = Test-Connection -ComputerName 8.8.8.8 -Count 1 -Quiet
        if ($pingResult) {
            Write-Host "   Acceso a Internet: OK" -ForegroundColor Green
            $connected = $true
        } else {
            Write-Host "   Sin acceso a Internet, esperando..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "   Intento $i/$maxIntentos - Esperando conexion..." -ForegroundColor Gray
    }
}

if (-not $connected) {
    Write-Host "   No se pudo conectar completamente a WCORP" -ForegroundColor Red
}

# 7. Actualizar GPO
Write-Host ""
Write-Host "7. Actualizando directivas de grupo..." -ForegroundColor Yellow
Start-Process -FilePath "gpupdate.exe" -ArgumentList "/force" -NoNewWindow -Wait
Write-Host "   Directivas actualizadas" -ForegroundColor Green

} catch {
    Write-Output "❌ ERROR EN POWERSHELL: $($_.Exception.Message)"
    Write-Output "StackTrace: $($_.ScriptStackTrace)"
}
'''


def ejecutar(executor: RemoteExecutor, hostname: str):
    """
    Ejecuta la solución de problemas WCORP en el equipo remoto
    
    Args:
        executor: Instancia de RemoteExecutor
        hostname: Nombre del equipo remoto
    """
    print(f"\n🔧 Solucionando problemas WCORP en {hostname}...")
    print("   (Este proceso puede tomar 2-3 minutos)")
    print()
    
    result = executor.run_script_block(hostname, SCRIPT_WCORP_FIX, timeout=300)
    
    if result:
        print(result)
    else:
        print("❌ Error ejecutando solución WCORP")
    
    print()
    input("Presioná ENTER para continuar...")


def main():
    """Función principal para ejecución standalone"""
    from utils.common import clear_screen
    
    clear_screen()
    print("=" * 60)
    print("🔧 SOLUCIÓN PROBLEMAS WCORP")
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

