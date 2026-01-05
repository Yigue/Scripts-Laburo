# Ejecutar NoSleep.exe para evitar que el equipo entre en suspensión

try {
    $nosleep = "C:\temp\NoSleep.exe"
    
    if (Test-Path $nosleep) {
        # Verificar si ya está corriendo
        $running = Get-Process -Name "NoSleep" -ErrorAction SilentlyContinue
        
        if ($running) {
            Write-Output "ℹ️ NoSleep ya está en ejecución"
        } else {
            Start-Process -FilePath $nosleep -WindowStyle Minimized
            Write-Output "✅ NoSleep iniciado"
        }
    } else {
        Write-Output "⚠️ NoSleep.exe no encontrado en $nosleep"
    }
} catch {
    Write-Output "⚠️ Error iniciando NoSleep: $($_.Exception.Message)"
}

