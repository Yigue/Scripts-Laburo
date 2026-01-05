"""
SystemMaintenance - Mantenimiento del sistema
Responsabilidad: SFC, DISM, limpieza, etc.
"""
from typing import Optional
from domain.models import Host, OperationResult
from infrastructure.resources import ScriptLoader


class SystemMaintenance:
    """Manejador especializado para tareas de mantenimiento del sistema"""
    
    def __init__(self, executor, script_loader: Optional[ScriptLoader] = None):
        """
        Inicializa el handler
        
        Args:
            executor: Ejecutor remoto
            script_loader: Cargador de scripts
        """
        self.executor = executor
        self.script_loader = script_loader or ScriptLoader()
    
    def run_sfc(self, host: Host, timeout: int = 900) -> OperationResult:
        """
        Ejecuta sfc /scannow en el host remoto
        
        Args:
            host: Host donde ejecutar SFC
            timeout: Timeout en segundos (default 15 minutos)
            
        Returns:
            OperationResult con el resultado
        """
        result = OperationResult(
            success=False,
            message="Ejecutando SFC /scannow"
        )
        
        try:
            print("   ⏱️ Esto puede tomar 10-15 minutos...")
            
            script = self.script_loader.load_with_wrapper(
                "hardware/configure_equipment",
                "run_sfc"
            )
            
            output = self.executor.run_script_block(
                host.hostname,
                script,
                timeout=timeout,
                verbose=False
            )
            
            if output:
                # Mostrar últimas líneas del output
                lines = output.strip().split('\n')
                for line in lines[-10:]:
                    print(f"   {line}")
                
                result.success = True
                result.message = "SFC ejecutado correctamente"
                result.data = output
            else:
                result.add_error("SFC no produjo salida")
                
        except Exception as e:
            result.add_error(f"Error ejecutando SFC: {e}")
        
        return result
    
    def run_dism(self, host: Host, timeout: int = 1200) -> OperationResult:
        """
        Ejecuta DISM /RestoreHealth
        
        Args:
            host: Host donde ejecutar DISM
            timeout: Timeout en segundos (default 20 minutos)
            
        Returns:
            OperationResult con el resultado
        """
        result = OperationResult(
            success=False,
            message="Ejecutando DISM"
        )
        
        try:
            script = """
Write-Output "🔍 Ejecutando DISM /RestoreHealth..."
Write-Output "⏱️ Esto puede tomar 15-20 minutos..."

try {
    $dism = Start-Process -FilePath "dism.exe" `
        -ArgumentList "/Online", "/Cleanup-Image", "/RestoreHealth" `
        -NoNewWindow -Wait -PassThru
    
    if ($dism.ExitCode -eq 0) {
        Write-Output "✅ DISM completado correctamente"
    } else {
        Write-Output "⚠️ DISM terminó con código: $($dism.ExitCode)"
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
                timeout=timeout,
                verbose=False
            )
            
            result.success = True
            result.message = "DISM ejecutado"
            result.data = output
            
        except Exception as e:
            result.add_error(f"Error ejecutando DISM: {e}")
        
        return result

