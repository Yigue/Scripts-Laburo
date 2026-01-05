# Suspender BitLocker por 1 reinicio
# Se usa antes de actualizar drivers o hacer cambios de hardware

try {
    $bl = Get-BitLockerVolume -MountPoint "C:" -ErrorAction SilentlyContinue
    
    if ($bl -and $bl.ProtectionStatus -eq "On") {
        Suspend-BitLocker -MountPoint "C:" -RebootCount 1 -ErrorAction Stop
        Write-Output "✅ BitLocker suspendido por 1 reinicio"
    } else {
        Write-Output "ℹ️ BitLocker no está activo o ya está suspendido"
    }
} catch {
    Write-Output "⚠️ No se pudo suspender BitLocker: $($_.Exception.Message)"
    Write-Output "Puede ser necesario hacerlo manualmente"
}

