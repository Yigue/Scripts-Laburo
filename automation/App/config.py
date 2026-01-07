"""
Configuración centralizada de la aplicación
Carga desde variables de entorno, archivo YAML o valores por defecto
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json


@dataclass
class AppConfig:
    """Configuración global de la aplicación"""
    
    # ============================================================================
    # PATHS DE RECURSOS
    # ============================================================================
    psexec_path: str = "PsExec.exe"
    remote_user: Optional[str] = None
    remote_pass: Optional[str] = None
    tools_network_path: str = r"\\pc101338\c$\Tools"
    dell_command_source: str = "Dell-Command-Update-Application_6VFWW_WIN_5.4.0_A00.EXE"
    nosleep_source: str = "NoSleep.exe"
    office_source_path: str = r"\\pc101338\c$\Tools\Office"
    
    # ============================================================================
    # TIMEOUTS
    # ============================================================================
    default_timeout: int = 120
    long_operation_timeout: int = 1800  # 30 min
    connection_timeout: int = 30
    
    # ============================================================================
    # EJECUCIÓN PARALELA
    # ============================================================================
    max_parallel_hosts: int = 5
    enable_parallel: bool = True
    max_retry_attempts: int = 3
    
    # ============================================================================
    # LOGGING
    # ============================================================================
    log_level: str = "INFO"
    log_dir: str = "data/logs"
    log_retention_days: int = 30
    log_max_bytes: int = 10 * 1024 * 1024  # 10 MB
    log_backup_count: int = 5
    
    # ============================================================================
    # CACHE
    # ============================================================================
    cache_enabled: bool = True
    cache_dir: str = "data/cache"
    cache_ttl_default: int = 300  # 5 minutos
    
    # ============================================================================
    # WinRM
    # ============================================================================
    winrm_port: int = 5985
    winrm_transport: str = "ntlm"
    winrm_verify_ssl: bool = False
    
    # ============================================================================
    # ANSIBLE
    # ============================================================================
    ansible_inventory: Optional[str] = None
    ansible_playbooks_dir: str = "automation/ansible/playbooks"
    
    def __post_init__(self):
        """Cargar configuración desde archivo si existe"""
        self._load_from_file()
        self._load_from_env()
    
    def _load_from_file(self):
        """Carga configuración desde config.json si existe"""
        config_file = Path("config.json")
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
            except Exception as e:
                print(f"Warning: No se pudo cargar config.json: {e}")
    
    def _load_from_env(self):
        """Carga configuración desde variables de entorno"""
        # Paths & Credentials
        if os.getenv('PSEXEC_PATH'):
            self.psexec_path = os.getenv('PSEXEC_PATH')
        if os.getenv('REMOTE_USER'):
            self.remote_user = os.getenv('REMOTE_USER')
        if os.getenv('REMOTE_PASS'):
            self.remote_pass = os.getenv('REMOTE_PASS')

        if os.getenv('TOOLS_NETWORK_PATH'):
            self.tools_network_path = os.getenv('TOOLS_NETWORK_PATH')
        
        # Timeouts
        if os.getenv('DEFAULT_TIMEOUT'):
            self.default_timeout = int(os.getenv('DEFAULT_TIMEOUT'))
        
        # Parallel
        if os.getenv('MAX_PARALLEL_HOSTS'):
            self.max_parallel_hosts = int(os.getenv('MAX_PARALLEL_HOSTS'))
        
        # Logging
        if os.getenv('LOG_LEVEL'):
            self.log_level = os.getenv('LOG_LEVEL')
    
    def save_to_file(self, filepath: str = "config.json"):
        """Guarda configuración actual a archivo JSON"""
        config_dict = {
            "tools_network_path": self.tools_network_path,
            "dell_command_source": self.dell_command_source,
            "office_source_path": self.office_source_path,
            "default_timeout": self.default_timeout,
            "max_parallel_hosts": self.max_parallel_hosts,
            "log_level": self.log_level,
            "cache_enabled": self.cache_enabled,
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=4)


# Instancia global de configuración
_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Obtiene la instancia global de configuración (singleton)
    
    Returns:
        AppConfig: Configuración de la aplicación
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance


def reload_config():
    """Recarga la configuración desde archivo"""
    global _config_instance
    _config_instance = AppConfig()
    return _config_instance

