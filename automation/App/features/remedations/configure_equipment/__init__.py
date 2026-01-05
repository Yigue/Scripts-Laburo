"""
Caso de uso: Configurar Equipo Completo
Orchestrator que coordina la configuración completa de un equipo nuevo
"""
from typing import Optional
import time
from domain.models import Host, OperationResult
from infrastructure.resources import ResourceManager, ScriptLoader
from shared.exceptions import AutomationError
from .bitlocker_handler import BitLockerHandler
from .resource_copier import ResourceCopier
from .system_maintenance import SystemMaintenance


class ConfigureEquipmentUseCase:
    """
    Caso de uso principal para configuración completa de equipo
    Coordina todas las operaciones necesarias en el orden correcto
    """
    
    def __init__(self, executor, resource_manager: Optional[ResourceManager] = None,
                 script_loader: Optional[ScriptLoader] = None):
        """
        Inicializa el caso de uso
        
        Args:
            executor: Ejecutor remoto (WinRM/PsExec/Ansible)
            resource_manager: Gestor de recursos
            script_loader: Cargador de scripts
        """
        self.executor = executor
        self.resource_manager = resource_manager or ResourceManager()
        self.script_loader = script_loader or ScriptLoader()
        
        # Inicializar handlers especializados
        self.bitlocker = BitLockerHandler(executor, script_loader)
        self.copier = ResourceCopier(executor, resource_manager)
        self.maintenance = SystemMaintenance(executor, script_loader)
    
    def execute(self, host: Host, skip_office: bool = False, 
                skip_drivers: bool = False, skip_sfc: bool = False) -> OperationResult:
        """
        Ejecuta configuración completa del equipo
        
        Args:
            host: Host a configurar
            skip_office: Si True, omite instalación de Office
            skip_drivers: Si True, omite actualización de drivers Dell
            skip_sfc: Si True, omite sfc /scannow
            
        Returns:
            OperationResult con resultado de la operación completa
        """
        result = OperationResult(
            success=False,
            message="Configuración de equipo iniciada",
            metadata={
                "hostname": host.hostname,
                "is_notebook": host.is_notebook,
                "start_time": time.time()
            }
        )
        
        try:
            print(f"\n🔧 CONFIGURACIÓN COMPLETA DE {host.hostname}")
            print("=" * 60)
            print("\nEste proceso incluye:")
            print("  1. Copiar recursos necesarios")
            print("  2. Suspender BitLocker (si es notebook)")
            print("  3. Instalar/actualizar Dell Command")
            if not skip_office:
                print("  4. Instalar Office 365")
            print("  5. Activar licencia Windows")
            if not skip_sfc:
                print("  6. Ejecutar SFC /scannow")
            print("  7. Reiniciar equipo")
            print("\n⏱️ Tiempo estimado: 30-60 minutos\n")
            
            confirmar = input("¿Continuar? (S/N): ").strip().upper()
            if confirmar != "S":
                result.message = "Operación cancelada por el usuario"
                return result
            
            start_time = time.time()
            
            # PASO 1: Crear carpeta TEMP
            self._execute_step(1, "Preparando carpeta TEMP", host, result)
            self._create_temp_folder(host)
            
            # PASO 2: Copiar recursos
            self._execute_step(2, "Copiando recursos", host, result)
            copy_result = self.copier.copy_all_resources(host)
            if not copy_result.success:
                result.add_warning("Algunos recursos no se pudieron copiar")
            
            # PASO 3: Iniciar NoSleep
            print("\n💤 Iniciando NoSleep...")
            self._run_nosleep(host)
            
            # PASO 4: Suspender BitLocker (solo notebooks)
            if host.is_notebook:
                self._execute_step(3, "Suspendiendo BitLocker", host, result)
                bl_result = self.bitlocker.suspend(host)
                if not bl_result.success:
                    result.add_warning(bl_result.message)
            else:
                print("\n" + "=" * 60)
                print("🔐 PASO 3/7: BitLocker (no aplica para PC)")
            
            # PASO 5: Dell Command Update
            if not skip_drivers:
                self._execute_step(4, "Dell Command Update", host, result)
                self._install_dell_command(host)
            
            # PASO 6: Office 365
            if not skip_office:
                self._execute_step(5, "Office 365", host, result)
                self._install_office(host)
            
            # PASO 7: Activar Windows
            self._execute_step(6, "Activando Windows", host, result)
            self._activate_windows(host)
            
            # PASO 8: SFC /scannow
            if not skip_sfc:
                self._execute_step(7, "Ejecutando SFC /scannow", host, result)
                sfc_result = self.maintenance.run_sfc(host)
                if not sfc_result.success:
                    result.add_warning(sfc_result.message)
            
            # Calcular tiempo total
            elapsed = time.time() - start_time
            elapsed_min = int(elapsed // 60)
            elapsed_sec = int(elapsed % 60)
            
            print("\n" + "=" * 60)
            print(f"✅ CONFIGURACIÓN COMPLETADA")
            print(f"   Tiempo total: {elapsed_min}m {elapsed_sec}s")
            print("=" * 60)
            
            result.success = True
            result.message = f"Configuración completada en {elapsed_min}m {elapsed_sec}s"
            result.metadata["elapsed_time"] = elapsed
            
            # Preguntar si reiniciar
            reiniciar = input("\n¿Reiniciar el equipo ahora? (S/N): ").strip().upper()
            if reiniciar == "S":
                self._restart_computer(host)
                result.metadata["restarted"] = True
            
        except AutomationError as e:
            result.add_error(str(e))
            result.message = f"Error en configuración: {e}"
        except KeyboardInterrupt:
            result.add_error("Operación interrumpida por el usuario")
            result.message = "Operación interrumpida"
        except Exception as e:
            result.add_error(f"Error inesperado: {e}")
            result.message = "Error inesperado en configuración"
        
        return result
    
    def _execute_step(self, step_num: int, step_name: str, host: Host, result: OperationResult):
        """Helper para mostrar información de paso"""
        print("\n" + "=" * 60)
        print(f"📋 PASO {step_num}/7: {step_name}")
    
    def _create_temp_folder(self, host: Host):
        """Crea carpeta C:\\TEMP en el equipo remoto"""
        script = self.script_loader.load_with_wrapper(
            "hardware/configure_equipment",
            "create_temp_folder"
        )
        self.executor.run_script_block(host.hostname, script, timeout=10, verbose=False)
    
    def _run_nosleep(self, host: Host):
        """Ejecuta NoSleep.exe"""
        script = self.script_loader.load_with_wrapper(
            "hardware/configure_equipment",
            "run_nosleep"
        )
        self.executor.run_script_block(host.hostname, script, timeout=10, verbose=False)
    
    def _install_dell_command(self, host: Host):
        """Instala y ejecuta Dell Command Update"""
        # Esta funcionalidad ya existe en dell_command.py
        # Aquí se delega a ese módulo
        from features.hardware import dell_command
        dell_command.ejecutar(self.executor, host.hostname, copiar=False)
    
    def _install_office(self, host: Host):
        """Instala Office 365"""
        # Esta funcionalidad ya existe en office_install.py
        # Aquí se delega a ese módulo
        from features.software import office_install
        office_install.ejecutar(self.executor, host.hostname)
    
    def _activate_windows(self, host: Host):
        """Activa licencia de Windows"""
        # Esta funcionalidad ya existe en activar_windows.py
        # Aquí se delega a ese módulo
        from features.hardware import activar_windows
        activar_windows.ejecutar(self.executor, host.hostname)
    
    def _restart_computer(self, host: Host):
        """Reinicia el equipo"""
        print(f"\n🔄 Reiniciando {host.hostname}...")
        self.executor.restart_computer(host.hostname, force=True, wait=False)
        print("   Comando de reinicio enviado")


def ejecutar(executor, hostname: str):
    """
    Función wrapper para compatibilidad con código existente
    
    Args:
        executor: Ejecutor remoto
        hostname: Nombre del host
    """
    host = Host(hostname=hostname)
    use_case = ConfigureEquipmentUseCase(executor)
    result = use_case.execute(host)
    
    if not result.success:
        print(f"\n❌ Errores encontrados:")
        for error in result.errors:
            print(f"   • {error}")
    
    if result.has_warnings:
        print(f"\n⚠️ Advertencias:")
        for warning in result.warnings:
            print(f"   • {warning}")
    
    input("\nPresioná ENTER para continuar...")


