"""
HealthChecker - Verificación de salud de hosts
"""
import subprocess
from typing import Dict, Any
from domain.models import Host
from domain.interfaces import IHealthChecker
from infrastructure.logging import get_logger


class HealthChecker(IHealthChecker):
    """
    Verificador de salud de hosts remotos
    Implementa IHealthChecker interface
    """
    
    def __init__(self, executor):
        """
        Inicializa el health checker
        
        Args:
            executor: Ejecutor remoto
        """
        self.executor = executor
        self.logger = get_logger()
    
    def check_connectivity(self, host: Host) -> Dict[str, Any]:
        """
        Verifica conectividad básica con el host
        
        Args:
            host: Host a verificar
            
        Returns:
            Dict con resultados del check
        """
        result = {
            "hostname": host.hostname,
            "ping": False,
            "winrm": False,
            "smb": False,
            "healthy": False
        }
        
        # Test 1: Ping
        try:
            ping_result = subprocess.run(
                ["ping", "-n", "1", "-w", "1000", host.hostname],
                capture_output=True,
                timeout=5
            )
            result["ping"] = ping_result.returncode == 0
        except Exception as e:
            self.logger.error(f"Ping failed for {host.hostname}: {e}")
        
        # Test 2: WinRM
        try:
            winrm_test = self.executor.test_connection(host.hostname)
            result["winrm"] = winrm_test
        except Exception as e:
            self.logger.error(f"WinRM test failed for {host.hostname}: {e}")
        
        # Test 3: SMB (C$)
        try:
            import os
            smb_path = f"\\\\{host.hostname}\\c$"
            result["smb"] = os.path.exists(smb_path)
        except Exception as e:
            self.logger.error(f"SMB test failed for {host.hostname}: {e}")
        
        # Determinar salud general
        result["healthy"] = result["ping"] and (result["winrm"] or result["smb"])
        
        return result
    
    def check_disk_space(self, host: Host, required_gb: float = 10.0) -> Dict[str, Any]:
        """
        Verifica espacio disponible en disco
        
        Args:
            host: Host a verificar
            required_gb: GB requeridos
            
        Returns:
            Dict con resultados
        """
        result = {
            "hostname": host.hostname,
            "free_gb": 0.0,
            "required_gb": required_gb,
            "sufficient": False,
            "error": None
        }
        
        try:
            script = """
$drive = Get-PSDrive -Name C
$freeGB = [math]::Round($drive.Free / 1GB, 2)
Write-Output $freeGB
"""
            output = self.executor.run_script_block(host.hostname, script, timeout=10)
            
            if output:
                free_gb = float(output.strip())
                result["free_gb"] = free_gb
                result["sufficient"] = free_gb >= required_gb
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"Disk space check failed for {host.hostname}: {e}")
        
        return result
    
    def check_prerequisites(self, host: Host, operation: str) -> Dict[str, Any]:
        """
        Verifica pre-requisitos para una operación específica
        
        Args:
            host: Host a verificar
            operation: Operación a ejecutar
            
        Returns:
            Dict con resultados
        """
        result = {
            "hostname": host.hostname,
            "operation": operation,
            "checks_passed": [],
            "checks_failed": [],
            "ready": False
        }
        
        # Checks básicos para cualquier operación
        connectivity = self.check_connectivity(host)
        if connectivity["healthy"]:
            result["checks_passed"].append("Conectividad OK")
        else:
            result["checks_failed"].append("Sin conectividad")
        
        # Checks específicos por operación
        if operation in ["configure_equipment", "install_office", "dell_command"]:
            disk = self.check_disk_space(host, required_gb=15.0)
            if disk["sufficient"]:
                result["checks_passed"].append(f"Espacio en disco: {disk['free_gb']:.1f} GB")
            else:
                result["checks_failed"].append(f"Espacio insuficiente: {disk['free_gb']:.1f} GB")
        
        result["ready"] = len(result["checks_failed"]) == 0
        
        return result

