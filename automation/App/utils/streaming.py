"""
Utilidad para ejecutar scripts remotos con streaming de salida en tiempo real.
Usa polling de archivo de log vía SMB para mostrar salida mientras se ejecuta.
"""
import os
import threading
import time
from typing import Optional, Callable


class LogFilePoller:
    """
    Lee un archivo de log remoto y muestra nuevas líneas en tiempo real.
    El archivo se accede vía SMB (\\\\hostname\\c$\\path).
    """
    
    def __init__(self, log_path: str, line_callback: Optional[Callable[[str], None]] = None):
        """
        Args:
            log_path: Ruta UNC al archivo de log (ej: \\\\HOST\\c$\\TEMP\\log.txt)
            line_callback: Función a llamar por cada línea nueva (default: print)
        """
        self.log_path = log_path
        self.line_callback = line_callback or self._default_callback
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_position = 0
        self._lines_shown = set()
    
    def _default_callback(self, line: str):
        """Callback por defecto: imprime la línea con indentación"""
        print(f"   {line}")
    
    def _poll_loop(self):
        """Loop principal que lee nuevas líneas del archivo"""
        while not self._stop_event.is_set():
            try:
                if os.path.exists(self.log_path):
                    with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(self._last_position)
                        new_content = f.read()
                        self._last_position = f.tell()
                        
                        if new_content:
                            for line in new_content.splitlines():
                                line = line.strip()
                                if line and line not in self._lines_shown:
                                    self._lines_shown.add(line)
                                    self.line_callback(line)
            except Exception:
                pass  # Ignorar errores de lectura
            
            time.sleep(0.5)  # Polling cada 500ms
    
    def start(self):
        """Inicia el polling en un thread separado"""
        self._stop_event.clear()
        self._last_position = 0
        self._lines_shown.clear()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Detiene el polling"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None


def run_with_streaming(executor, hostname: str, script: str, 
                       operation_name: str = "Operación",
                       timeout: int = 1800,
                       log_filename: str = "operation.log") -> Optional[str]:
    """
    Ejecuta un script remoto mostrando la salida en tiempo real.
    
    Args:
        executor: RemoteExecutor instance
        hostname: Nombre del host remoto
        script: Script PowerShell a ejecutar (debe usar Log function)
        operation_name: Nombre de la operación para mostrar
        timeout: Timeout en segundos
        log_filename: Nombre del archivo de log
    
    Returns:
        str: Salida completa del script o None si falló
    """
    # Ruta del log
    log_path = f"\\\\{hostname}\\c$\\TEMP\\{log_filename}"
    
    # Limpiar log anterior via script rápido
    clear_script = f'''
    $logFile = "C:\\TEMP\\{log_filename}"
    if (Test-Path $logFile) {{ Remove-Item $logFile -Force }}
    "" | Set-Content $logFile -Encoding UTF8
    '''
    executor.run_script_block(hostname, clear_script, timeout=10, verbose=False)
    
    # Iniciar poller
    poller = LogFilePoller(log_path)
    poller.start()
    
    try:
        # Ejecutar script principal (esto bloquea hasta completar)
        result = executor.run_script_block(hostname, script, timeout=timeout, verbose=False)
        
        # Esperar un momento para capturar últimas líneas
        time.sleep(1)
        
        return result
        
    finally:
        poller.stop()


def wrap_script_with_logging(script: str, log_filename: str = "operation.log") -> str:
    """
    Envuelve un script PowerShell para que escriba a un archivo de log.
    
    Args:
        script: Script PowerShell original
        log_filename: Nombre del archivo de log
    
    Returns:
        str: Script modificado con logging
    """
    header = f'''
$global:LogFile = "C:\\TEMP\\{log_filename}"

# Función para logging con salida a archivo Y consola
function Log {{
    param([string]$Message, [string]$Color = "White")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logMessage = $Message
    $logMessage | Add-Content $global:LogFile -Encoding UTF8
    Write-Output $logMessage
}}

# Inicializar log
"" | Set-Content $global:LogFile -Encoding UTF8

'''
    return header + script
