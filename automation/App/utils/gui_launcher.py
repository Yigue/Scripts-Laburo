import sys
import threading
import importlib
import io
import time
from presentation.gui.output_window import OutputWindow
from utils.remote_executor import RemoteExecutor

class GlobalThreadRedirector:
    """Redirige stdout de forma selectiva según el hilo que llama"""
    def __init__(self):
        self._targets = {}
        self._lock = threading.Lock()
        self._original_stdout = sys.stdout

    def register_thread(self, thread_id, callback):
        with self._lock:
            self._targets[thread_id] = callback

    def unregister_thread(self, thread_id):
        with self._lock:
            if thread_id in self._targets:
                del self._targets[thread_id]

    def write(self, string):
        if not string: return
        tid = threading.get_ident()
        with self._lock:
            callback = self._targets.get(tid)
        
        if callback:
            callback(string.strip())
        
        # También escribir en la consola original para debugging/fallback
        self._original_stdout.write(string)

    def flush(self):
        self._original_stdout.flush()

# Única instancia global de redirección
_GLOBAL_REDIRECTOR = GlobalThreadRedirector()
sys.stdout = _GLOBAL_REDIRECTOR

def launch_operation_in_gui(module_path: str, hostname: str, label: str):
    """
    Lanza una operación en un hilo separado y muestra su salida en una ventana GUI.
    Maneja la cancelación si el usuario presiona "Detener".
    """
    window = OutputWindow(hostname, label)
    
    def run_task():
        current_thread = threading.current_thread()
        _GLOBAL_REDIRECTOR.register_thread(current_thread.ident, window.log)
        
        # Thread para monitoreo de cancelación
        def monitor_cancel(exec_process_done):
            while not exec_process_done.is_set():
                if window.is_stopped():
                    # Ejecutar script remoto para matar procesos del usuario
                    # Este es un "fire and forget" rápido
                    kill_executor = RemoteExecutor()
                    kill_script = f'''
                    $currentUser = $env:USERNAME
                    $processes = Get-CimInstance Win32_Process -Filter "Name != 'wsmprovhost.exe' AND Name != 'svchost.exe'" 
                    foreach ($p in $processes) {{
                        try {{
                            if ($p.GetOwner().User -eq $currentUser) {{
                                Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
                            }}
                        }} catch {{}}
                    }}
                    '''
                    kill_executor.run_script_block(hostname, kill_script, silent=True, verbose=False)
                    break
                time.sleep(1)

        exec_done = threading.Event()
        monitor_thread = threading.Thread(target=monitor_cancel, args=(exec_done,), daemon=True)
        monitor_thread.start()
        
        try:
            # Importar dinámicamente
            module = importlib.import_module(module_path)
            if not hasattr(module, 'ejecutar'):
                window.log(f"Error: El módulo {module_path} no tiene función ejecutar()")
                window.set_finished(False)
                return
            
            # Ejecutar con el executor (hereda Admin)
            executor = RemoteExecutor()
            module.ejecutar(executor, hostname)
            
            # Verificar si se detuvo manualmente
            if window.is_stopped():
                window.set_finished(False, reason="CANCELLED")
            else:
                # Verificar error
                last_error = executor.get_last_error()
                if last_error:
                    window.log(f"\n[ERROR]: {last_error}")
                    window.set_finished(False)
                else:
                    window.set_finished(True)
                
        except Exception as e:
            if window.is_stopped():
                window.set_finished(False, reason="CANCELLED")
            else:
                window.log(f"\nError fatal: {str(e)}")
                import traceback
                window.log(traceback.format_exc())
                window.set_finished(False)
        finally:
            exec_done.set()
            _GLOBAL_REDIRECTOR.unregister_thread(current_thread.ident)

    # Lanzar hilos
    exec_thread = threading.Thread(target=run_task, daemon=True)
    exec_thread.start()
    
    gui_thread = threading.Thread(target=window.run, daemon=True)
    gui_thread.start()
