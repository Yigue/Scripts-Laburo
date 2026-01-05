# Crear carpeta C:\TEMP si no existe

try {
    $folder = "C:\TEMP"
    
    if (!(Test-Path $folder)) {
        New-Item -Path $folder -ItemType Directory -Force | Out-Null
        Write-Output "✅ Carpeta TEMP creada: $folder"
    } else {
        Write-Output "ℹ️ Carpeta TEMP ya existe"
    }
} catch {
    Write-Output "❌ Error creando carpeta TEMP: $($_.Exception.Message)"
    throw
}

