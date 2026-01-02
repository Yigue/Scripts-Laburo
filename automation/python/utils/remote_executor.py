"""
Ejecutor remoto unificado con fallback automático WinRM → PsExec
Intenta WinRM primero, si falla intenta PsExec automáticamente
"""
from typing import Optional
from dataclasses import dataclass

from .winrm import WinRMExecutor, WinRMConfig, test_winrm_connection
from .psexec import PsExecExecutor, PsExecConfig, test_psexec_connection


@dataclass
class RemoteExecResult:
    """Resultado de ejecución remota"""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    method_used: str  # "winrm", "psexec", "none"
    error: Optional[str] = None


class RemoteExecutor:
    """
    Ejecutor remoto unificado con fallback automático
    
    Estrategia:
    1. Intenta WinRM usando pypsrp (sesión actual o credenciales)
    2. Si WinRM falla, intenta PsExec usando pypsexec (si hay credenciales y puerto 445 abierto)
    3. Muestra errores detallados con diagnóstico
    """
    
    def __init__(self):
        """Inicializa el ejecutor remoto"""
        self.winrm_config = WinRMConfig()
        self.psexec_config = PsExecConfig()
        self.winrm_executor = WinRMExecutor(self.winrm_config)
        self.psexec_executor = PsExecExecutor(self.psexec_config)
        self._last_error = None
        self._preferred_method = None  # Se detecta automáticamente
    
    def test_connection(self, hostname: str, verbose: bool = True) -> dict:
        """
        Prueba conexión con ambos métodos y determina el preferido
        
        Args:
            hostname: Nombre del host remoto
            verbose: Si True, muestra mensajes
        
        Returns:
            dict: Resultado de las pruebas con método preferido
        """
        result = {
            "hostname": hostname,
            "winrm_available": False,
            "psexec_available": False,
            "preferred_method": None,
            "ready": False,
            "errors": []
        }
        
        def log(msg):
            if verbose:
                print(msg)
        
        # Probar WinRM
        log(f"🔍 Probando WinRM en {hostname}...")
        winrm_ok, winrm_error = test_winrm_connection(hostname, self.winrm_config)
        result["winrm_available"] = winrm_ok
        
        if winrm_ok:
            log("   ✅ WinRM disponible")
            result["preferred_method"] = "winrm"
            result["ready"] = True
        else:
            if winrm_error:
                result["errors"].append(f"WinRM: {winrm_error}")
            log(f"   ❌ WinRM no disponible: {winrm_error or 'Error desconocido'}")
        
        # Probar PsExec solo si WinRM falló
        if not winrm_ok:
            log(f"🔍 Probando PsExec en {hostname}...")
            psexec_ok, psexec_error, psexec_details = test_psexec_connection(hostname, self.psexec_config)
            result["psexec_available"] = psexec_ok
            
            if psexec_ok:
                log("   ✅ PsExec disponible")
                result["preferred_method"] = "psexec"
                result["ready"] = True
            else:
                if psexec_error:
                    result["errors"].append(f"PsExec: {psexec_error}")
                log(f"   ❌ PsExec no disponible: {psexec_error or 'Error desconocido'}")
        
        self._preferred_method = result["preferred_method"]
        return result
    
    def execute_ps(self, hostname: str, script: str, timeout: int = 120, verbose: bool = True) -> RemoteExecResult:
        """
        Ejecuta un script PowerShell en el host remoto con fallback automático
        
        Args:
            hostname: Nombre del host remoto
            script: Script PowerShell a ejecutar
            timeout: Timeout en segundos
            verbose: Si True, muestra mensajes de progreso
        
        Returns:
            RemoteExecResult: Resultado de la ejecución
        """
        if verbose:
            preview = script[:100] + ("..." if len(script) > 100 else "")
            print(f"▶ Ejecutando en {hostname}: {preview}")
        
        # Intentar WinRM primero
        if verbose:
            print("   [1/2] Intentando WinRM...")
        
        winrm_result = self.winrm_executor.execute_ps(hostname, script, timeout=timeout)
        
        if winrm_result.success:
            if verbose:
                print(f"   ✅ WinRM exitoso")
            self._last_error = None
            return RemoteExecResult(
                success=True,
                stdout=winrm_result.stdout,
                stderr=winrm_result.stderr,
                return_code=winrm_result.return_code,
                method_used="winrm",
                error=None
            )
        
        # WinRM falló, intentar PsExec
        if verbose:
            print(f"   ⚠ WinRM falló: {winrm_result.error}")
            print("   [2/2] Intentando PsExec...")
        
        # Verificar que PsExec sea viable
        if not self.psexec_config.has_credentials():
            error = "PsExec no disponible: no hay credenciales configuradas"
            self._last_error = error
            if verbose:
                print(f"   ❌ {error}")
            return RemoteExecResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                method_used="none",
                error=f"WinRM falló: {winrm_result.error}. PsExec no disponible: {error}"
            )
        
        psexec_result = self.psexec_executor.execute_ps(hostname, script, timeout)
        
        if psexec_result.success:
            if verbose:
                print(f"   ✅ PsExec exitoso")
            self._last_error = None
            return RemoteExecResult(
                success=True,
                stdout=psexec_result.stdout,
                stderr=psexec_result.stderr,
                return_code=psexec_result.return_code,
                method_used="psexec",
                error=None
            )
        
        # Ambos fallaron
        error = f"Ambos métodos fallaron. WinRM: {winrm_result.error}. PsExec: {psexec_result.error}"
        self._last_error = error
        if verbose:
            print(f"   ❌ {error}")
        return RemoteExecResult(
            success=False,
            stdout="",
            stderr="",
            return_code=-1,
            method_used="none",
            error=error
        )
    
    def execute_command(self, hostname: str, command: str, arguments: Optional[list] = None, timeout: int = 60, verbose: bool = True) -> RemoteExecResult:
        """
        Ejecuta un comando en el host remoto con fallback automático
        
        Args:
            hostname: Nombre del host remoto
            command: Comando a ejecutar
            arguments: Argumentos del comando (opcional)
            timeout: Timeout en segundos
            verbose: Si True, muestra mensajes
        
        Returns:
            RemoteExecResult: Resultado de la ejecución
        """
        # Convertir comando a script PowerShell
        if arguments:
            args_str = " ".join(str(arg) for arg in arguments)
            script = f"{command} {args_str}"
        else:
            script = command
        
        return self.execute_ps(hostname, script, timeout, verbose)
    
    def run_command(self, hostname: str, command: str, timeout: int = 60, verbose: bool = True) -> Optional[str]:
        """
        Ejecuta un comando y retorna solo stdout si fue exitoso
        
        Args:
            hostname: Nombre del host remoto
            command: Comando a ejecutar
            timeout: Timeout en segundos
            verbose: Si True, muestra mensajes
        
        Returns:
            str: Salida del comando o None si falló
        """
        result = self.execute_command(hostname, command, timeout=timeout, verbose=verbose)
        return result.stdout if result.success else None
    
    def run_script_block(self, hostname: str, script_block: str, timeout: int = 120, verbose: bool = True) -> Optional[str]:
        """
        Ejecuta un bloque de script PowerShell
        
        Args:
            hostname: Nombre del host remoto
            script_block: Script PowerShell a ejecutar
            timeout: Timeout en segundos
            verbose: Si True, muestra mensajes
        
        Returns:
            str: Salida del script o None si falló
        """
        result = self.execute_ps(hostname, script_block, timeout=timeout, verbose=verbose)
        return result.stdout if result.success else None
    
    def get_last_error(self) -> Optional[str]:
        """Retorna el último error ocurrido"""
        return self._last_error

