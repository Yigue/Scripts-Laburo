# Ejecutar sfc /scannow para verificar integridad de archivos del sistema

Write-Output "🔍 Ejecutando sfc /scannow..."
Write-Output "⏱️ Esto puede tomar 10-15 minutos..."

try {
    $sfc = Start-Process -FilePath "sfc.exe" -ArgumentList "/scannow" -NoNewWindow -Wait -PassThru
    
    if ($sfc.ExitCode -eq 0) {
        Write-Output "✅ SFC completado correctamente"
    } else {
        Write-Output "⚠️ SFC terminó con código: $($sfc.ExitCode)"
    }
    
    # Mostrar log si está disponible
    $logPath = "$env:windir\Logs\CBS\CBS.log"
    if (Test-Path $logPath) {
        Write-Output ""
        Write-Output "📄 Últimas líneas del log:"
        Get-Content $logPath -Tail 10 | ForEach-Object { Write-Output "   $_" }
    }
} catch {
    Write-Output "❌ Error ejecutando SFC: $($_.Exception.Message)"
    throw
}

