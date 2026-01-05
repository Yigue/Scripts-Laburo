"""
Ejecutor remoto unificado con fallback automático WinRM → PsExec
Protocolo Andreani IT: Zero-Auth (SSO) con fallback inteligente
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
    
    Protocolo de conexión (Andreani IT):
    1. Pre-check de disponibilidad (ping + puertos 5985/445)
    2. Canal A (WinRM/PSRP): Conexión primaria con SSO/Kerberos
    3. Canal B (PsExec/SMB): Fallback automático si WinRM falla
    """
    
    def __init__(self):
        """Inicializa el ejecutor remoto con configuración SSO"""
        self.winrm_config = WinRMConfig()
        self.psexec_config = PsExecConfig()
        self.winrm_executor = WinRMExecutor(self.winrm_config)
        self.psexec_executor = PsExecExecutor(self.psexec_config)
        self._last_error = None
        self._preferred_method = None
        self._connection_tested = False
    
    def test_connection(self, hostname: str, verbose: bool = True) -> dict:
        """
        Prueba conexión y determina el método preferido
        
        Args:
            hostname: Nombre del host remoto
            verbose: Si True, muestra mensajes de estado
        
        Returns:
            dict: Estado de conexión con método preferido
        """
        result = {
            "hostname": hostname,
            "winrm_available": False,
            "psexec_available": False,
            "preferred_method": None,
            "ready": False,
            "errors": []
        }
        
        # Probar WinRM primero (Canal A)
        if verbose:
            print(f"   🔍 Verificando conectividad con {hostname}...")
        
        winrm_ok, winrm_error = test_winrm_connection(hostname, self.winrm_config)
        result["winrm_available"] = winrm_ok
        
        if winrm_ok:
            if verbose:
                print(f"   ✅ Conexión WinRM establecida")
            result["preferred_method"] = "winrm"
            result["ready"] = True
            self._preferred_method = "winrm"
            self._connection_tested = True
            return result
        
        # WinRM falló - verificar si es error de DNS (no intentar PsExec)
        error_lower = (winrm_error or "").lower()
        is_fatal_error = any(keyword in error_lower for keyword in [
            "dns", "resolve", "getaddrinfo", "name resolution", "failed to resolve",
            "no existe", "not found"
        ])
        
        if is_fatal_error:
            if verbose:
                print(f"   ❌ Host no accesible: {self._format_error(winrm_error)}")
            result["errors"].append(winrm_error)
            self._last_error = winrm_error
            return result
        
        # Intentar PsExec como fallback (Canal B)
        if verbose:
            print(f"   🔄 WinRM no disponible, probando canal alternativo...")
        
        psexec_ok, psexec_error, _ = test_psexec_connection(hostname, self.psexec_config)
        result["psexec_available"] = psexec_ok
        
        if psexec_ok:
            if verbose:
                print(f"   ✅ Conexión PsExec establecida")
            result["preferred_method"] = "psexec"
            result["ready"] = True
            self._preferred_method = "psexec"
        else:
            if verbose:
                print(f"   ❌ Sin métodos de conexión disponibles")
            result["errors"].extend([winrm_error or "", psexec_error or ""])
            self._last_error = f"WinRM: {winrm_error}. PsExec: {psexec_error}"
        
        self._connection_tested = True
        return result
    
    def execute_ps(self, hostname: str, script: str, timeout: int = 120, verbose: bool = True) -> RemoteExecResult:
        """
        Ejecuta un script PowerShell con fallback automático
        
        Args:
            hostname: Nombre del host remoto
            script: Script PowerShell a ejecutar
            timeout: Timeout en segundos
            verbose: Si True, muestra indicadores de progreso
        
        Returns:
            RemoteExecResult: Resultado de la ejecución
        """
        if verbose:
            print(f"   🔄 Conectando...", end="", flush=True)
        
        # Intentar WinRM primero (Canal A)
        winrm_result = self.winrm_executor.execute_ps(hostname, script, timeout=timeout)
        
        if winrm_result.success:
            if verbose:
                print(f" ✅ OK")
            self._last_error = None
            return RemoteExecResult(
                success=True,
                stdout=winrm_result.stdout,
                stderr=winrm_result.stderr,
                return_code=winrm_result.return_code,
                method_used="winrm",
                error=None
            )
        
        # WinRM falló - verificar si debemos intentar PsExec
        error_lower = (winrm_result.error or "").lower()
        is_fatal_error = any(keyword in error_lower for keyword in [
            "dns", "resolve", "getaddrinfo", "name resolution", "failed to resolve"
        ])
        
        if is_fatal_error:
            if verbose:
                print(f" ❌ Error de red")
            self._last_error = winrm_result.error
            return RemoteExecResult(
                success=False,
                stdout="",
                stderr="",
                return_code=-1,
                method_used="none",
                error=self._format_error(winrm_result.error)
            )
        
        # Intentar PsExec como fallback (Canal B)
        if verbose:
            print(f" ⚠️ Fallback...", end="", flush=True)
        
        psexec_result = self.psexec_executor.execute_ps(hostname, script, timeout)
        
        if psexec_result.success:
            if verbose:
                print(f" ✅ OK")
            self._last_error = None
            return RemoteExecResult(
                success=True,
                stdout=psexec_result.stdout,
                stderr=psexec_result.stderr,
                return_code=psexec_result.return_code,
                method_used="psexec",
                error=None
            )
        
        # Ambos métodos fallaron
        if verbose:
            print(f" ❌ Error")
        
        self._last_error = f"WinRM: {self._format_error(winrm_result.error)}. PsExec: {self._format_error(psexec_result.error)}"
        return RemoteExecResult(
            success=False,
            stdout="",
            stderr="",
            return_code=-1,
            method_used="none",
            error=self._last_error
        )
    
    def run_script_block(self, hostname: str, script_block: str, timeout: int = 120, verbose: bool = True) -> Optional[str]:
        """
        Ejecuta un bloque de script PowerShell y retorna la salida
        
        Args:
            hostname: Nombre del host remoto
            script_block: Script PowerShell a ejecutar
            timeout: Timeout en segundos
            verbose: Si True, muestra indicadores de progreso
        
        Returns:
            str: Salida del script o None si falló
        """
        result = self.execute_ps(hostname, script_block, timeout=timeout, verbose=verbose)
        if result.success:
            return result.stdout if result.stdout else "(sin salida)"
        return None
    
    def run_command(self, hostname: str, command: str, timeout: int = 60, verbose: bool = True) -> Optional[str]:
        """
        Ejecuta un comando y retorna la salida
        
        Args:
            hostname: Nombre del host remoto
            command: Comando a ejecutar
            timeout: Timeout en segundos
            verbose: Si True, muestra indicadores
        
        Returns:
            str: Salida del comando o None si falló
        """
        result = self.execute_ps(hostname, command, timeout=timeout, verbose=verbose)
        if result.success:
            output = result.stdout
            if result.stderr:
                output = f"{output}\n{result.stderr}" if output else result.stderr
            return output if output else None
        return None
    
    def restart_computer(self, hostname: str, force: bool = True, wait: bool = False, timeout: int = 30) -> bool:
        """
        Reinicia el equipo remoto
        
        Args:
            hostname: Nombre del host remoto
            force: Si True, fuerza el reinicio sin esperar aplicaciones
            wait: Reservado para uso futuro
            timeout: Timeout del comando
        
        Returns:
            bool: True si el comando se envió exitosamente
        """
        script = "Restart-Computer -Force -ErrorAction Stop" if force else "Restart-Computer -ErrorAction Stop"
        result = self.execute_ps(hostname, script, timeout=timeout, verbose=False)
        return result.success
    
    def test_ping(self, hostname: str, count: int = 1, timeout: int = 3) -> bool:
        """
        Prueba conectividad básica con ping
        
        Args:
            hostname: Nombre del host
            count: Número de pings (reservado)
            timeout: Timeout en segundos
        
        Returns:
            bool: True si responde al ping
        """
        from .conection.network_utils import test_ping as ping_test
        return ping_test(hostname, timeout)
    
    def get_last_error(self) -> Optional[str]:
        """Retorna el último error ocurrido"""
        return self._last_error
    
    def _format_error(self, error: Optional[str]) -> str:
        """
        Formatea un mensaje de error para mostrarlo de forma limpia
        
        Args:
            error: Mensaje de error original
        
        Returns:
            str: Mensaje formateado (más corto y legible)
        """
        if not error:
            return "Error desconocido"
        
        # Truncar mensajes muy largos
        if len(error) > 150:
            # Buscar la parte más relevante
            if ":" in error:
                parts = error.split(":")
                # Tomar las primeras partes significativas
                return ":".join(parts[:2]).strip()[:150]
            return error[:150] + "..."
        
        return error
