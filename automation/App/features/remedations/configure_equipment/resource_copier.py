"""
ResourceCopier - Copia de recursos al host remoto
Responsabilidad: Copiar archivos/instaladores necesarios
"""
from typing import List, Optional
from domain.models import Host, OperationResult
from infrastructure.resources import ResourceManager
from config import get_config


class ResourceCopier:
    """Copiador especializado de recursos a hosts remotos"""
    
    def __init__(self, executor, resource_manager: Optional[ResourceManager] = None):
        """
        Inicializa el copiador
        
        Args:
            executor: Ejecutor remoto
            resource_manager: Gestor de recursos
        """
        self.executor = executor
        self.resource_manager = resource_manager or ResourceManager()
        self.config = get_config()
    
    def copy_all_resources(self, host: Host, verbose: bool = True) -> OperationResult:
        """
        Copia todos los recursos necesarios para configuración completa
        
        Args:
            host: Host destino
            verbose: Si True, muestra progreso
            
        Returns:
            OperationResult con resultado de la operación
        """
        result = OperationResult(
            success=True,
            message="Copiando recursos",
            data={}
        )
        
        # Lista de recursos a copiar
        resources = [
            self.config.dell_command_source,
            self.config.nosleep_source,
        ]
        
        for resource in resources:
            if verbose:
                print(f"📦 Copiando {resource}...")
            
            success = self.resource_manager.copy_to_remote(host, resource)
            result.data[resource] = success
            
            if success:
                if verbose:
                    print(f"   ✅ {resource} copiado")
            else:
                result.add_warning(f"No se pudo copiar {resource}")
                result.success = False
        
        # Copiar Office (setup.exe y config.xml)
        if verbose:
            print("📦 Copiando Office 365...")
        
        office_success = self._copy_office_resources(host)
        result.data["office"] = office_success
        
        if office_success:
            if verbose:
                print("   ✅ Office 365 copiado")
        else:
            result.add_warning("No se pudieron copiar archivos de Office")
        
        return result
    
    def _copy_office_resources(self, host: Host) -> bool:
        """
        Copia recursos de Office al host remoto
        
        Args:
            host: Host destino
            
        Returns:
            bool: True si la copia fue exitosa
        """
        try:
            import os
            import shutil
            
            office_source = self.config.office_source_path
            remote_temp = f"\\\\{host.hostname}\\c$\\Temp"
            
            # Crear directorio si no existe
            os.makedirs(remote_temp, exist_ok=True)
            
            # Copiar setup.exe
            setup_source = os.path.join(office_source, "setup.exe")
            setup_dest = os.path.join(remote_temp, "setup.exe")
            
            if os.path.exists(setup_source):
                shutil.copy2(setup_source, setup_dest)
            else:
                return False
            
            # Copiar config.xml
            config_source = os.path.join(office_source, "config.xml")
            config_dest = os.path.join(remote_temp, "config.xml")
            
            if os.path.exists(config_source):
                shutil.copy2(config_source, config_dest)
            else:
                return False
            
            return True
            
        except Exception as e:
            print(f"⚠️ Error copiando Office: {e}")
            return False

