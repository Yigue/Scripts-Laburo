# Lista servicios del sistema con su estado

try {
    Write-Output "🔧 SERVICIOS DEL SISTEMA"
    Write-Output ("=" * 70)
    Write-Output ""
    
    # Obtener servicios
    $services = Get-Service | Sort-Object Status, DisplayName
    
    # Agrupar por estado
    $running = $services | Where-Object { $_.Status -eq 'Running' }
    $stopped = $services | Where-Object { $_.Status -eq 'Stopped' }
    
    Write-Output "📊 Resumen:"
    Write-Output "   En ejecución: $($running.Count)"
    Write-Output "   Detenidos: $($stopped.Count)"
    Write-Output "   Total: $($services.Count)"
    Write-Output ""
    Write-Output ("=" * 70)
    Write-Output ""
    
    # Mostrar servicios en ejecución
    Write-Output "✅ SERVICIOS EN EJECUCIÓN:"
    Write-Output ""
    $running | Format-Table Name, DisplayName, Status -AutoSize | Out-String | Write-Output
    
    Write-Output ""
    Write-Output ("=" * 70)
    Write-Output ""
    
    # Mostrar servicios con problemas
    $problematic = Get-Service | Where-Object { 
        $_.StartType -eq 'Automatic' -and $_.Status -ne 'Running' 
    }
    
    if ($problematic) {
        Write-Output "⚠️ SERVICIOS AUTOMÁTICOS DETENIDOS:"
        Write-Output ""
        $problematic | Format-Table Name, DisplayName, Status, StartType -AutoSize | Out-String | Write-Output
    }
    
    Write-Output ""
    Write-Output "✅ Lista de servicios generada"
} catch {
    Write-Output "❌ ERROR: $($_.Exception.Message)"
    throw
}

