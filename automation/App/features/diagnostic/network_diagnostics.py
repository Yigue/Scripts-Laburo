"""
Caso de uso: Diagnósticos de Red
Permite realizar diagnósticos de red, ping, flush DNS, etc.
"""
from typing import Optional
from domain.models import Host, OperationResult
from infrastructure.resources import ScriptLoader
from infrastructure.logging import get_logger


class NetworkDiagnosticsUseCase:
    """Caso de uso para diagnósticos de red"""
    
    def __init__(self, executor, script_loader: Optional[ScriptLoader] = None):
        self.executor = executor
        self.script_loader = script_loader or ScriptLoader()
        self.logger = get_logger()
    
    def run_diagnostics(self, host: Host) -> OperationResult:
        """Ejecuta diagnósticos completos de red"""
        result = OperationResult(success=False, message="Ejecutando diagnósticos")
        
        try:
            print(f"\n🌐 Ejecutando diagnósticos de red en {host.hostname}...\n")
            
            script = self.script_loader.load_with_wrapper("network", "network_diagnostics")
            output = self.executor.run_script_block(host.hostname, script, timeout=60, verbose=False)
            
            if output:
                print(output)
                result.success = True
                result.data = output
            else:
                result.add_error("No se obtuvo información")
        except Exception as e:
            result.add_error(f"Error: {e}")
            self.logger.log_exception("Error en run_diagnostics", e)
        
        return result
    
    def flush_dns(self, host: Host) -> OperationResult:
        """Limpia caché DNS"""
        result = OperationResult(success=False, message="Limpiando caché DNS")
        
        try:
            print(f"\n🔄 Limpiando caché DNS en {host.hostname}...\n")
            
            script = """
try {
    ipconfig /flushdns
    Write-Output "✅ Caché DNS limpiado"
} catch {
    Write-Output "❌ ERROR: $($_.Exception.Message)"
    throw
}
"""
            wrapped = self.script_loader.load("common", "write_host_redirect") + "\n" + script
            output = self.executor.run_script_block(host.hostname, wrapped, timeout=30, verbose=False)
            
            if output:
                print(output)
                result.success = "✅" in output
                result.data = output
        except Exception as e:
            result.add_error(f"Error: {e}")
        
        return result
    
    def ping_test(self, host: Host, target: str) -> OperationResult:
        """Ejecuta ping a un destino"""
        result = OperationResult(success=False, message=f"Ping a {target}")
        
        try:
            print(f"\n🏓 Ejecutando ping a {target}...\n")
            
            script = f"""
try {{
    $result = Test-Connection -ComputerName "{target}" -Count 4 -ErrorAction Stop
    
    Write-Output "🏓 Ping a {target}:"
    Write-Output ""
    
    foreach ($r in $result) {{
        Write-Output "Respuesta de $($r.Address): tiempo=$($r.ResponseTime)ms TTL=$($r.TimeToLive)"
    }}
    
    $avg = ($result | Measure-Object -Property ResponseTime -Average).Average
    Write-Output ""
    Write-Output "Tiempo promedio: $([math]::Round($avg, 2))ms"
    Write-Output "✅ Ping exitoso"
}} catch {{
    Write-Output "❌ Ping fallido: $($_.Exception.Message)"
    throw
}}
"""
            wrapped = self.script_loader.load("common", "write_host_redirect") + "\n" + script
            output = self.executor.run_script_block(host.hostname, wrapped, timeout=30, verbose=False)
            
            if output:
                print(output)
                result.success = "✅" in output
                result.data = output
        except Exception as e:
            result.add_error(f"Error: {e}")
        
        return result
    
    def show_menu(self, host: Host):
        """Muestra menú de diagnósticos de red"""
        while True:
            print(f"\n{'=' * 60}")
            print(f"🌐 DIAGNÓSTICOS DE RED - {host.hostname}")
            print("=" * 60)
            print()
            print("1. Ejecutar diagnósticos completos")
            print("2. Limpiar caché DNS")
            print("3. Ping a destino")
            print()
            print("0. Volver")
            print("=" * 60)
            
            opcion = input("\nSeleccioná una opción: ").strip()
            
            if opcion == "1":
                self.run_diagnostics(host)
                input("\nPresioná ENTER para continuar...")
            elif opcion == "2":
                self.flush_dns(host)
                input("\nPresioná ENTER para continuar...")
            elif opcion == "3":
                target = input("\nIngresá destino (IP o hostname): ").strip()
                if target:
                    self.ping_test(host, target)
                input("\nPresioná ENTER para continuar...")
            elif opcion == "0":
                break


def ejecutar(executor, hostname: str):
    """Función wrapper para compatibilidad"""
    host = Host(hostname=hostname)
    use_case = NetworkDiagnosticsUseCase(executor)
    use_case.show_menu(host)

