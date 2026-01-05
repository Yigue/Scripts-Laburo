"""
Caso de uso: Gestión de Servicios
Permite listar, iniciar, detener y configurar servicios de Windows
"""
from typing import Optional
from domain.models import Host, OperationResult
from infrastructure.resources import ScriptLoader
from infrastructure.logging import get_logger


class ServiceManagementUseCase:
    """Caso de uso para gestión de servicios"""
    
    def __init__(self, executor, script_loader: Optional[ScriptLoader] = None):
        self.executor = executor
        self.script_loader = script_loader or ScriptLoader()
        self.logger = get_logger()
    
    def list_services(self, host: Host) -> OperationResult:
        """Lista servicios del sistema"""
        result = OperationResult(success=False, message="Listando servicios")
        
        try:
            print(f"\n🔧 Listando servicios en {host.hostname}...\n")
            
            script = self.script_loader.load_with_wrapper("sistema", "list_services")
            output = self.executor.run_script_block(host.hostname, script, timeout=60, verbose=False)
            
            if output:
                print(output)
                result.success = True
                result.data = output
            else:
                result.add_error("No se obtuvo información")
        except Exception as e:
            result.add_error(f"Error: {e}")
            self.logger.log_exception("Error en list_services", e)
        
        return result
    
    def control_service(self, host: Host, service_name: str, action: str) -> OperationResult:
        """Controla un servicio (start/stop/restart)"""
        result = OperationResult(success=False, message=f"{action} servicio {service_name}")
        
        try:
            actions_map = {
                "start": "Start-Service",
                "stop": "Stop-Service",
                "restart": "Restart-Service"
            }
            
            if action not in actions_map:
                result.add_error(f"Acción inválida: {action}")
                return result
            
            ps_command = actions_map[action]
            
            script = f"""
try {{
    $service = Get-Service -Name "{service_name}" -ErrorAction Stop
    Write-Output "Servicio: $($service.DisplayName)"
    Write-Output "Estado actual: $($service.Status)"
    Write-Output ""
    
    {ps_command} -Name "{service_name}" -ErrorAction Stop
    
    Start-Sleep -Seconds 2
    $service = Get-Service -Name "{service_name}"
    
    Write-Output "✅ Acción completada"
    Write-Output "Nuevo estado: $($service.Status)"
}} catch {{
    Write-Output "❌ ERROR: $($_.Exception.Message)"
    throw
}}
"""
            wrapped = self.script_loader.load("common", "write_host_redirect") + "\n" + script
            output = self.executor.run_script_block(host.hostname, wrapped, timeout=60, verbose=False)
            
            if output:
                print(output)
                result.success = "✅" in output
                result.data = output
        except Exception as e:
            result.add_error(f"Error: {e}")
        
        return result
    
    def show_menu(self, host: Host):
        """Muestra menú de gestión de servicios"""
        while True:
            print(f"\n{'=' * 60}")
            print(f"🔧 GESTIÓN DE SERVICIOS - {host.hostname}")
            print("=" * 60)
            print()
            print("1. Listar servicios")
            print("2. Iniciar servicio")
            print("3. Detener servicio")
            print("4. Reiniciar servicio")
            print()
            print("0. Volver")
            print("=" * 60)
            
            opcion = input("\nSeleccioná una opción: ").strip()
            
            if opcion == "1":
                self.list_services(host)
                input("\nPresioná ENTER para continuar...")
            elif opcion in ["2", "3", "4"]:
                service_name = input("\nIngresá el nombre del servicio: ").strip()
                if service_name:
                    action_map = {"2": "start", "3": "stop", "4": "restart"}
                    self.control_service(host, service_name, action_map[opcion])
                input("\nPresioná ENTER para continuar...")
            elif opcion == "0":
                break


def ejecutar(executor, hostname: str):
    """Función wrapper para compatibilidad"""
    host = Host(hostname=hostname)
    use_case = ServiceManagementUseCase(executor)
    use_case.show_menu(host)

