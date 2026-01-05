"""
Caso de uso: Gestión de Aplicaciones Instaladas
Permite listar, buscar y desinstalar aplicaciones en hosts remotos
"""
from typing import Optional, List, Dict
from dataclasses import dataclass
from domain.models import Host, OperationResult
from infrastructure.resources import ScriptLoader
from infrastructure.logging import get_logger


@dataclass
class Application:
    """Representación de una aplicación instalada"""
    index: int
    name: str
    version: str
    publisher: str


class ManageApplicationsUseCase:
    """
    Caso de uso para gestión de aplicaciones instaladas
    Coordina operaciones de listar, buscar y desinstalar aplicaciones
    """
    
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
    
    def list_applications(self, host: Host) -> OperationResult:
        """
        Lista todas las aplicaciones instaladas en el host
        
        Args:
            host: Host donde listar aplicaciones
            
        Returns:
            OperationResult con lista de aplicaciones
        """
        result = OperationResult(
            success=False,
            message="Listando aplicaciones instaladas"
        )
        
        try:
            print(f"\n📦 Listando aplicaciones instaladas en {host.hostname}...")
            print("   Esto puede tomar unos segundos...\n")
            
            script = self.script_loader.load_with_wrapper(
                "software/applications",
                "list_apps"
            )
            
            output = self.executor.run_script_block(
                host.hostname,
                script,
                timeout=60,
                verbose=False
            )
            
            if output:
                print(output)
                result.success = True
                result.message = "Aplicaciones listadas correctamente"
                result.data = output
                
                self.logger.log_operation(
                    host.hostname,
                    "list_applications",
                    True,
                    0.0
                )
            else:
                result.add_error("No se obtuvo salida del comando")
                
        except Exception as e:
            result.add_error(f"Error listando aplicaciones: {e}")
            self.logger.log_exception("Error en list_applications", e)
        
        return result
    
    def search_applications(self, host: Host, search_term: str) -> OperationResult:
        """
        Busca aplicaciones por nombre
        
        Args:
            host: Host donde buscar
            search_term: Término de búsqueda
            
        Returns:
            OperationResult con resultados de búsqueda
        """
        result = OperationResult(
            success=False,
            message=f"Buscando '{search_term}'"
        )
        
        try:
            print(f"\n🔍 Buscando aplicaciones con: '{search_term}'...\n")
            
            # Cargar script y reemplazar parámetro
            script = self.script_loader.load("software/applications", "search_apps")
            
            # Construir script completo con parámetro
            redirect = self.script_loader.load("common", "write_host_redirect")
            full_script = f"""{redirect}

try {{
    $SearchTerm = "{search_term}"
{self._indent_script(script, 4)}
}} catch {{
    Write-Output "❌ ERROR: $($_.Exception.Message)"
    throw
}}
"""
            
            output = self.executor.run_script_block(
                host.hostname,
                full_script,
                timeout=30,
                verbose=False
            )
            
            if output:
                print(output)
                result.success = True
                result.message = "Búsqueda completada"
                result.data = output
            else:
                result.add_error("No se obtuvo salida")
                
        except Exception as e:
            result.add_error(f"Error buscando: {e}")
            self.logger.log_exception("Error en search_applications", e)
        
        return result
    
    def uninstall_application(self, host: Host, app_index: int) -> OperationResult:
        """
        Desinstala una aplicación por su índice
        
        Args:
            host: Host donde desinstalar
            app_index: Índice de la aplicación a desinstalar
            
        Returns:
            OperationResult con resultado de desinstalación
        """
        result = OperationResult(
            success=False,
            message=f"Desinstalando aplicación #{app_index}"
        )
        
        try:
            print(f"\n🗑️ Desinstalando aplicación #{app_index}...")
            print("   Esto puede tomar varios minutos...\n")
            
            # Cargar script y reemplazar parámetro
            script = self.script_loader.load("software/applications", "uninstall_app")
            
            # Construir script completo con parámetro
            redirect = self.script_loader.load("common", "write_host_redirect")
            full_script = f"""{redirect}

try {{
    $AppIndex = {app_index}
{self._indent_script(script, 4)}
}} catch {{
    Write-Output "❌ ERROR: $($_.Exception.Message)"
    throw
}}
"""
            
            output = self.executor.run_script_block(
                host.hostname,
                full_script,
                timeout=300,  # 5 minutos para desinstalación
                verbose=False
            )
            
            if output:
                print(output)
                result.success = "✅" in output or "completada" in output.lower()
                result.message = "Desinstalación procesada"
                result.data = output
                
                self.logger.log_operation(
                    host.hostname,
                    f"uninstall_app_{app_index}",
                    result.success,
                    0.0
                )
            else:
                result.add_error("No se obtuvo salida")
                
        except Exception as e:
            result.add_error(f"Error desinstalando: {e}")
            self.logger.log_exception("Error en uninstall_application", e)
        
        return result
    
    def show_menu(self, host: Host):
        """
        Muestra menú interactivo de gestión de aplicaciones
        
        Args:
            host: Host donde gestionar aplicaciones
        """
        while True:
            print(f"\n{'=' * 60}")
            print(f"📦 GESTIÓN DE APLICACIONES - {host.hostname}")
            print("=" * 60)
            print()
            print("1. Listar todas las aplicaciones")
            print("2. Buscar aplicación")
            print("3. Desinstalar aplicación")
            print()
            print("0. Volver")
            print("=" * 60)
            
            opcion = input("\nSeleccioná una opción: ").strip()
            
            if opcion == "1":
                self.list_applications(host)
                input("\nPresioná ENTER para continuar...")
                
            elif opcion == "2":
                busqueda = input("\nIngresá término de búsqueda: ").strip()
                if busqueda:
                    self.search_applications(host, busqueda)
                input("\nPresioná ENTER para continuar...")
                
            elif opcion == "3":
                try:
                    indice = int(input("\nIngresá el índice de la aplicación: ").strip())
                    
                    confirmacion = input(f"\n⚠️ ¿Confirmar desinstalación de aplicación #{indice}? (S/N): ").strip().upper()
                    if confirmacion == "S":
                        self.uninstall_application(host, indice)
                    else:
                        print("\nDesinstalación cancelada")
                        
                except ValueError:
                    print("\n❌ Índice inválido")
                    
                input("\nPresioná ENTER para continuar...")
                
            elif opcion == "0":
                break
            else:
                print("\n❌ Opción inválida")
                input("\nPresioná ENTER para continuar...")
    
    def _indent_script(self, script: str, spaces: int = 4) -> str:
        """Indenta un script con el número de espacios especificado"""
        indent = " " * spaces
        lines = script.split('\n')
        # No indentar líneas que ya empiezan con param o try/catch
        result = []
        for line in lines:
            if line.strip().startswith(('param', 'try {', '} catch {', 'catch {')):
                result.append(line)
            else:
                result.append(indent + line if line.strip() else line)
        return '\n'.join(result)


def ejecutar(executor, hostname: str):
    """
    Función wrapper para compatibilidad con código existente
    
    Args:
        executor: Ejecutor remoto
        hostname: Nombre del host
    """
    host = Host(hostname=hostname)
    use_case = ManageApplicationsUseCase(executor)
    use_case.show_menu(host)

