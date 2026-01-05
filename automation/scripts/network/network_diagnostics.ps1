# Diagnósticos de red completos

try {
    Write-Output "🌐 DIAGNÓSTICOS DE RED"
    Write-Output ("=" * 70)
    Write-Output ""
    
    # Configuración de adaptadores
    Write-Output "📡 ADAPTADORES DE RED:"
    Write-Output ""
    $adapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' }
    
    foreach ($adapter in $adapters) {
        Write-Output "Adaptador: $($adapter.Name)"
        Write-Output "   Estado: $($adapter.Status)"
        Write-Output "   Velocidad: $($adapter.LinkSpeed)"
        Write-Output "   MAC: $($adapter.MacAddress)"
        
        # Obtener configuración IP
        $ipconfig = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -ErrorAction SilentlyContinue | 
            Where-Object { $_.AddressFamily -eq 'IPv4' }
        
        if ($ipconfig) {
            Write-Output "   IP: $($ipconfig.IPAddress)"
            Write-Output "   Máscara: $($ipconfig.PrefixLength)"
        }
        Write-Output ""
    }
    
    # Gateway predeterminado
    Write-Output ("=" * 70)
    Write-Output "🚪 GATEWAY PREDETERMINADO:"
    Write-Output ""
    $gateway = Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($gateway) {
        Write-Output "Gateway: $($gateway.NextHop)"
    }
    Write-Output ""
    
    # Servidores DNS
    Write-Output ("=" * 70)
    Write-Output "🔍 SERVIDORES DNS:"
    Write-Output ""
    $dns = Get-DnsClientServerAddress -AddressFamily IPv4 | 
        Where-Object { $_.ServerAddresses.Count -gt 0 }
    
    foreach ($d in $dns) {
        Write-Output "Interfaz: $($d.InterfaceAlias)"
        foreach ($server in $d.ServerAddresses) {
            Write-Output "   DNS: $server"
        }
    }
    Write-Output ""
    
    # Conexiones activas
    Write-Output ("=" * 70)
    Write-Output "🔗 CONEXIONES ACTIVAS (establecidas):"
    Write-Output ""
    $connections = Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue | 
        Select-Object -First 10 LocalAddress, LocalPort, RemoteAddress, RemotePort, State
    
    if ($connections) {
        $connections | Format-Table -AutoSize | Out-String | Write-Output
    }
    
    Write-Output ""
    Write-Output "✅ Diagnósticos de red completados"
} catch {
    Write-Output "❌ ERROR: $($_.Exception.Message)"
    throw
}

