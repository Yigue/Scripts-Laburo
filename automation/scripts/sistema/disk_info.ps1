# Muestra información detallada de discos

try {
    Write-Output "💾 INFORMACIÓN DE DISCOS"
    Write-Output ("=" * 60)
    Write-Output ""
    
    # Información de volúmenes
    $volumes = Get-Volume | Where-Object { $_.DriveType -eq 'Fixed' }
    
    foreach ($vol in $volumes) {
        $driveLetter = if ($vol.DriveLetter) { "$($vol.DriveLetter):" } else { "Sin letra" }
        $sizeGB = [math]::Round($vol.Size / 1GB, 2)
        $freeGB = [math]::Round($vol.SizeRemaining / 1GB, 2)
        $usedGB = $sizeGB - $freeGB
        $percentUsed = if ($sizeGB -gt 0) { [math]::Round(($usedGB / $sizeGB) * 100, 1) } else { 0 }
        
        Write-Output "📂 Volumen: $driveLetter - $($vol.FileSystemLabel)"
        Write-Output "   Tamaño total: $sizeGB GB"
        Write-Output "   Espacio usado: $usedGB GB ($percentUsed%)"
        Write-Output "   Espacio libre: $freeGB GB"
        Write-Output "   Sistema de archivos: $($vol.FileSystem)"
        Write-Output "   Estado: $($vol.HealthStatus)"
        Write-Output ""
    }
    
    # Información de discos físicos
    Write-Output ("=" * 60)
    Write-Output "🔧 DISCOS FÍSICOS"
    Write-Output ("=" * 60)
    Write-Output ""
    
    $disks = Get-PhysicalDisk
    
    foreach ($disk in $disks) {
        $sizeGB = [math]::Round($disk.Size / 1GB, 2)
        
        Write-Output "💿 Disco: $($disk.DeviceId) - $($disk.FriendlyName)"
        Write-Output "   Tamaño: $sizeGB GB"
        Write-Output "   Tipo: $($disk.MediaType)"
        Write-Output "   Bus: $($disk.BusType)"
        Write-Output "   Estado: $($disk.HealthStatus)"
        Write-Output "   Operacional: $($disk.OperationalStatus)"
        Write-Output ""
    }
    
    Write-Output "✅ Información de discos recopilada"
} catch {
    Write-Output "❌ ERROR: $($_.Exception.Message)"
    throw
}

