"""
BitLockerHandler - Manejo de BitLocker
Responsabilidad: Suspender/Reanudar BitLocker
"""
from typing import Optional
from domain.models import Host, OperationResult
from infrastructure.resources import ScriptLoader


class BitLockerHandler:
    """Manejador especializado para operaciones de BitLocker"""
    
    def __init__(self, executor, script_loader: Optional[ScriptLoader] = None):
        """
        Inicializa el handler
        
        Args:
            executor: Ejecutor remoto
            script_loader: Cargador de scripts
        """
        self.executor = executor
        self.script_loader = script_loader or ScriptLoader()
    
    def suspend(self, host: Host, reboot_count: int = 1) -> OperationResult:
        """
        Suspende BitLocker por N reinicios
        
        Args:
            host: Host donde suspender BitLocker
            reboot_count: Número de reinicios que permanecerá suspendido
            
        Returns:
            OperationResult con el resultado de la operación
        """
        result = OperationResult(
            success=False,
            message="Suspendiendo BitLocker"
        )
        
        try:
            script = self.script_loader.load_with_wrapper(
                "hardware/configure_equipment",
                "suspend_bitlocker"
            )
            
            output = self.executor.run_script_block(
                host.hostname,
                script,
                timeout=30,
                verbose=False
            )
            
            if output:
                print(f"   {output}")
                result.success = True
                result.message = "BitLocker suspendido correctamente"
                result.data = output
            else:
                result.add_error("No se pudo suspender BitLocker")
                
        except Exception as e:
            result.add_error(f"Error suspendiendo BitLocker: {e}")
        
        return result
    
    def resume(self, host: Host) -> OperationResult:
        """
        Reanuda protección de BitLocker
        
        Args:
            host: Host donde reanudar BitLocker
            
        Returns:
            OperationResult con el resultado
        """
        result = OperationResult(
            success=False,
            message="Reanudando BitLocker"
        )
        
        try:
            # Script para reanudar BitLocker
            script = """
try {
    $bl = Get-BitLockerVolume -MountPoint "C:" -ErrorAction SilentlyContinue
    if ($bl -and $bl.ProtectionStatus -eq "Off") {
        Resume-BitLocker -MountPoint "C:" -ErrorAction Stop
        Write-Output "✅ BitLocker reanudado"
    } else {
        Write-Output "ℹ️ BitLocker ya está activo"
    }
} catch {
    Write-Output "❌ Error: $($_.Exception.Message)"
    throw
}
"""
            wrapped = self.script_loader.load("common", "write_host_redirect") + "\n" + script
            
            output = self.executor.run_script_block(
                host.hostname,
                wrapped,
                timeout=30,
                verbose=False
            )
            
            result.success = True
            result.message = "BitLocker reanudado"
            result.data = output
            
        except Exception as e:
            result.add_error(f"Error reanudando BitLocker: {e}")
        
        return result

