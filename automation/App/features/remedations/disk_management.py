"""
Caso de uso: Gestión de Discos
Permite ver información de discos, limpiar temporales, analizar espacio
"""
from typing import Optional
from domain.models import Host, OperationResult
from infrastructure.resources import ScriptLoader
from infrastructure.logging import get_logger


class DiskManagementUseCase:
    """Caso de uso para gestión de discos"""
    
    def __init__(self, executor, script_loader: Optional[ScriptLoader] = None):
        """
        Inicializa el caso de uso
        
        Args:
            executor: Ejecutor remoto
            script_loader: Cargador de scripts
        """
        self.executor = executor
        self.script_loader = script_loader or ScriptLoader()
        self.logger = get_logger()
    
    def show_disk_info(self, host: Host) -> OperationResult:
        """
        Muestra información detallada de discos
        
        Args:
            host: Host donde consultar
            
        Returns:
            OperationResult con información de discos
        """
        result = OperationResult(success=False, message="Consultando información de discos")
        
        try:
            print(f"\n💾 Consultando discos en {host.hostname}...\n")
            
            script = self.script_loader.load_with_wrapper("sistema", "disk_info")
            
            output = self.executor.run_script_block(host.hostname, script, timeout=30, verbose=False)
            
            if output:
                print(output)
                result.success = True
                result.message = "Información obtenida"
                result.data = output
            else:
                result.add_error("No se obtuvo información")
                
        except Exception as e:
            result.add_error(f"Error: {e}")
            self.logger.log_exception("Error en show_disk_info", e)
        
        return result
    
    def clean_temp_files(self, host: Host) -> OperationResult:
        """
        Limpia archivos temporales
        
        Args:
            host: Host donde limpiar
            
        Returns:
            OperationResult con resultado de limpieza
        """
        result = OperationResult(success=False, message="Limpiando archivos temporales")
        
        try:
            print(f"\n🧹 Limpiando archivos temporales en {host.hostname}...")
            print("   Esto puede tomar varios minutos...\n")
            
            script = """
try {
    $locations = @(
        "$env:TEMP",
        "$env:windir\\Temp",
        "$env:LOCALAPPDATA\\Microsoft\\Windows\\INetCache"
    )
    
    $totalFreed = 0
    
    foreach ($location in $locations) {
        if (Test-Path $location) {
            Write-Output "Limpiando: $location"
            
            $before = (Get-ChildItem -Path $location -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            
            Get-ChildItem -Path $location -Recurse -Force -ErrorAction SilentlyContinue | 
                Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
            
            $after = (Get-ChildItem -Path $location -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            $freed = if ($before) { ($before - $after) / 1MB } else { 0 }
            $totalFreed += $freed
            
            Write-Output "   Liberados: $([math]::Round($freed, 2)) MB"
        }
    }
    
    Write-Output ""
    Write-Output "✅ Total liberado: $([math]::Round($totalFreed, 2)) MB"
} catch {
    Write-Output "❌ ERROR: $($_.Exception.Message)"
    throw
}
"""
            wrapped = self.script_loader.load("common", "write_host_redirect") + "\n" + script
            
            output = self.executor.run_script_block(host.hostname, wrapped, timeout=180, verbose=False)
            
            if output:
                print(output)
                result.success = True
                result.message = "Limpieza completada"
                result.data = output
            else:
                result.add_error("No se obtuvo salida")
                
        except Exception as e:
            result.add_error(f"Error: {e}")
            self.logger.log_exception("Error en clean_temp_files", e)
        
        return result
    
    def show_menu(self, host: Host):
        """Muestra menú de gestión de discos"""
        while True:
            print(f"\n{'=' * 60}")
            print(f"💾 GESTIÓN DE DISCOS - {host.hostname}")
            print("=" * 60)
            print()
            print("1. Ver información de discos")
            print("2. Limpiar archivos temporales")
            print()
            print("0. Volver")
            print("=" * 60)
            
            opcion = input("\nSeleccioná una opción: ").strip()
            
            if opcion == "1":
                self.show_disk_info(host)
                input("\nPresioná ENTER para continuar...")
            elif opcion == "2":
                confirm = input("\n⚠️ ¿Confirmar limpieza de temporales? (S/N): ").strip().upper()
                if confirm == "S":
                    self.clean_temp_files(host)
                input("\nPresioná ENTER para continuar...")
            elif opcion == "0":
                break


def ejecutar(executor, hostname: str):
    """Función wrapper para compatibilidad"""
    host = Host(hostname=hostname)
    use_case = DiskManagementUseCase(executor)
    use_case.show_menu(host)

