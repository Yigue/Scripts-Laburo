"""
ResourceManager - Gestión centralizada de recursos (archivos, instaladores)
"""
import os
import shutil
from pathlib import Path
from typing import Optional
from config import get_config
from shared.exceptions import ResourceNotFoundError
from domain.interfaces import IResourceManager
from domain.models import Host


class ResourceManager(IResourceManager):
    """
    Gestor centralizado de recursos
    Maneja paths de instaladores, copia de archivos a hosts remotos, etc.
    """
    
    def __init__(self):
        self.config = get_config()
    
    def get_resource_path(self, resource_name: str) -> str:
        """
        Obtiene path completo de un recurso
        
        Args:
            resource_name: Nombre del recurso
            
        Returns:
            str: Path completo del recurso
            
        Raises:
            ResourceNotFoundError: Si el recurso no existe
        """
        # Buscar en path de red
        network_path = os.path.join(self.config.tools_network_path, resource_name)
        
        if os.path.exists(network_path):
            return network_path
        
        # Buscar en path local (para testing)
        local_path = os.path.join("resources", resource_name)
        if os.path.exists(local_path):
            return local_path
        
        raise ResourceNotFoundError(f"Recurso no encontrado: {resource_name}")
    
    def copy_to_remote(self, host: Host, resource_name: str, destination: str = "C:\\TEMP") -> bool:
        """
        Copia un recurso al host remoto
        
        Args:
            host: Host destino
            resource_name: Nombre del recurso a copiar
            destination: Directorio destino en el host remoto
            
        Returns:
            bool: True si la copia fue exitosa
            
        Raises:
            ResourceNotFoundError: Si el recurso no existe
        """
        try:
            # Obtener path del recurso
            source_path = self.get_resource_path(resource_name)
            
            # Construir path remoto (\\hostname\c$\TEMP)
            remote_path = f"\\\\{host.hostname}\\c$\\{destination.replace('C:\\', '')}"
            
            # Crear directorio si no existe
            os.makedirs(remote_path, exist_ok=True)
            
            # Copiar archivo
            dest_file = os.path.join(remote_path, os.path.basename(resource_name))
            shutil.copy2(source_path, dest_file)
            
            return True
            
        except Exception as e:
            print(f"Error copiando recurso {resource_name} a {host.hostname}: {e}")
            return False
    
    def verify_resource_exists(self, resource_name: str) -> bool:
        """
        Verifica si un recurso existe
        
        Args:
            resource_name: Nombre del recurso
            
        Returns:
            bool: True si existe
        """
        try:
            self.get_resource_path(resource_name)
            return True
        except ResourceNotFoundError:
            return False
    
    def copy_multiple(self, host: Host, resources: list, destination: str = "C:\\TEMP") -> dict:
        """
        Copia múltiples recursos al host remoto
        
        Args:
            host: Host destino
            resources: Lista de nombres de recursos
            destination: Directorio destino
            
        Returns:
            dict: {resource_name: success}
        """
        results = {}
        for resource in resources:
            results[resource] = self.copy_to_remote(host, resource, destination)
        return results
    
    def get_dell_command_installer(self) -> str:
        """Obtiene path del instalador de Dell Command"""
        return self.get_resource_path(self.config.dell_command_source)
    
    def get_nosleep_exe(self) -> str:
        """Obtiene path de NoSleep.exe"""
        return self.get_resource_path(self.config.nosleep_source)
    
    def get_office_installer(self) -> tuple:
        """
        Obtiene paths de instalador de Office (setup.exe y config.xml)
        
        Returns:
            tuple: (setup_path, config_path)
        """
        office_path = self.config.office_source_path
        setup_path = os.path.join(office_path, "setup.exe")
        config_path = os.path.join(office_path, "config.xml")
        
        if not os.path.exists(setup_path):
            raise ResourceNotFoundError(f"setup.exe no encontrado en {office_path}")
        if not os.path.exists(config_path):
            raise ResourceNotFoundError(f"config.xml no encontrado en {office_path}")
        
        return setup_path, config_path

