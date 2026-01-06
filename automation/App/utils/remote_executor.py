"""
Ejecutor remoto unificado con fallback automático WinRM → PsExec
Protocolo Andreani IT: Zero-Auth (SSO) con fallback inteligente
"""
from typing import Optional
from dataclasses import dataclass
import threading
import time

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
    Ejecutor remoto unificado con soporte para WinRM y PsExec como fallback,
    con sesiones persistentes y diagnóstico proactivo.
    """

    def __init__(self):
        """Inicializa el ejecutor con caché de sesiones."""
        self.winrm_config = WinRMConfig()
        self.psexec_config = PsExecConfig()
        self.winrm_executor = WinRMExecutor(self.winrm_config)
        self.psexec_executor = PsExecExecutor(self.psexec_config)
        self._sessions = {}  # Caché de sesiones WinRM: {hostname: WinRMSession}
        self._last_error = None
        self._lock = threading.Lock()
        self._thread_local = threading.local()

    def _get_winrm_session(self, hostname: str) -> WinRMSession:
        """Obtiene o crea una sesión WinRM persistente para el host."""
        with self._lock:
            if hostname in self._sessions:
                session = self._sessions[hostname]
                # Verificar si la sesión sigue abierta (opcional, pypsrp suele manejarlo)
                return session
            
            from .winrm.session import WinRMSession
            session = WinRMSession(hostname, self.winrm_config)
            session.connect()
            self._sessions[hostname] = session
            return session

    def close_sessions(self):
        """Cierra todas las sesiones persistentes."""
        with self._lock:
            for session in self._sessions.values():
                try:
                    session.close()
                except:
                    pass
            self._sessions.clear()

    @staticmethod
    def _test_port(hostname: str, port: int, timeout: int = 2) -> bool:
        """Prueba si un puerto está abierto."""
        import socket
        try:
            with socket.create_connection((hostname, port), timeout=timeout):
                return True
        except:
            return False

    def test_connection(self, hostname: str, verbose: bool = True) -> dict:
        """
        Diagnóstico proactivo de conexión secuencial (Ping -> Puertos -> Auth).
        """
        status = {
            "ready": False,
            "method": "None",
            "diagnostics": [],
            "error": None
        }

        if verbose:
            print(f"   🔍 Analizando {hostname}...")

        # 1. Prueba de red (Ping)
        from .conection.network_utils import test_ping
        if test_ping(hostname, timeout=2):
            status["diagnostics"].append("✅ Red: Responde PING.")
        else:
            status["diagnostics"].append("⚠️ Red: NO responde PING (ICMP bloqueado o equipo apagado).")

        # 2. Prueba de Puertos WinRM
        port = self.winrm_config.port
        if self._test_port(hostname, port):
            status["diagnostics"].append(f"✅ WinRM: Puerto {port} abierto.")
            # 3. Prueba de Autenticación WinRM
            try:
                self._get_winrm_session(hostname)
                status["diagnostics"].append("✅ Auth: WinRM autenticado correctamente.")
                status["ready"] = True
                status["method"] = "WinRM"
                return status
            except Exception as e:
                err = str(e)
                status["diagnostics"].append(f"❌ Auth: Error de WinRM ({err[:100]}...).")
                if "account is locked" in err.lower() or "0xc0000234" in err:
                    status["error"] = "CUENTA BLOQUEADA en Active Directory."
                    return status
        else:
            status["diagnostics"].append(f"❌ WinRM: Puerto {port} cerrado.")

        # 4. Fallback a PsExec (verificar SMB puerto 445)
        if self._test_port(hostname, 445):
            status["diagnostics"].append("✅ PsExec: Puerto SMB (445) abierto. Disponible como fallback.")
            status["ready"] = True
            status["method"] = "PsExec"
        else:
            status["diagnostics"].append("❌ PsExec: Puerto SMB (445) cerrado.")
            status["error"] = "Sin acceso por WinRM ni SMB."

        return status

    def run_script_block(self, hostname: str, script: str, timeout: int = 120, silent: bool = False, verbose: bool = True) -> Optional[str]:
        """
        Ejecuta un script con persistencia y reintentos (máx 2).
        """
        import time
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                if verbose and not silent:
                    print(f"   🔄 Exec [{attempt+1}/{max_retries}] en {hostname}...", end="", flush=True)
                
                # Intentar WinRM con sesión persistente
                try:
                    session = self._get_winrm_session(hostname)
                    stdout, stderr, rc = session.execute_ps(script)
                    
                    if rc == 0:
                        if verbose and not silent: print(" ✅ OK")
                        self._last_error = None
                        return stdout or "(sin salida)"
                    else:
                        if verbose and not silent: print(" ⚠️ OK (con errores)")
                        self._last_error = stderr
                        return f"{stdout}\n[ERROR]: {stderr}" if stdout else stderr

                except (Exception) as winrm_err:
                    # Si falla WinRM, invalidamos sesión y vemos si reintentamos o fallback
                    with self._lock:
                        if hostname in self._sessions:
                            del self._sessions[hostname]
                    
                    # Si es error de red/timeout, reintentar. Si es auth, fallback directo.
                    err_str = str(winrm_err).lower()
                    if "auth" in err_str or "credential" in err_str:
                        raise winrm_err # Forzar fallback
                    
                    if attempt < max_retries - 1:
                        if verbose and not silent: print(" 🔄 Reintentando...")
                        time.sleep(1)
                        continue
                    raise winrm_err

            except Exception as e:
                if verbose and not silent: print(" ⚠️ Fallback a PsExec...")
                res = self.psexec_executor.execute_ps(hostname, script, timeout)
                if res.success:
                    self._last_error = None
                    return res.stdout or "(sin salida)"
                else:
                    self._last_error = res.error or res.stderr
                    if verbose and not silent: print(f" ❌ Fallido: {self._last_error[:50]}")
                    return None

        return None

    def run_command(self, hostname: str, command: str, timeout: int = 60, verbose: bool = True) -> Optional[str]:
        """Envuelve run_script_block para comandos directos."""
        return self.run_script_block(hostname, command, timeout, verbose=verbose)

    def get_last_error(self) -> Optional[str]:
        return self._last_error

    def _format_error(self, error: Optional[str]) -> str:
        if not error: return "Error desconocido"
        return error[:200] + "..." if len(error) > 200 else error

