"""
Módulo helper para ejecución remota usando PsExec
Refactorizado desde Especificacioens.py para uso reutilizable
"""
import subprocess
import os
from datetime import datetime


class PsExecHelper:
    """Clase helper para ejecutar comandos remotos usando PsExec"""
    
    def __init__(self, psexec_path="PsExec.exe", remote_user="Administrador", remote_pass=""):
        """
        Inicializa el helper de PsExec
        
        Args:
            psexec_path: Ruta al ejecutable PsExec.exe
            remote_user: Usuario remoto para autenticación
            remote_pass: Contraseña remota (vacío si se usa LAPS)
        """
        self.psexec_path = psexec_path
        self.remote_user = remote_user
        self.remote_pass = remote_pass
    
    def run_remote(self, hostname, command, timeout=30, verbose=True):
        """
        Ejecuta un comando PowerShell remoto usando PsExec
        
        Args:
            hostname: Nombre del host remoto (ej: NB036595)
            command: Comando PowerShell a ejecutar
            timeout: Timeout en segundos
            verbose: Si True, muestra errores en consola
        
        Returns:
            str: Salida del comando o "N/A" si falla
        """
        # Escapar comillas dobles en el comando para PowerShell
        escaped_command = command.replace('"', '\\"')
        cmd = (
            f'{self.psexec_path} \\\\{hostname} -u "{self.remote_user}" -p "{self.remote_pass}" '
            f'powershell -NoProfile -Command "{escaped_command}"'
        )
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # Limpiar líneas de PsExec (líneas que empiezan con el nombre del host)
                lines = [
                    line for line in output.split('\n')
                    if line.strip() and not line.strip().startswith(hostname)
                ]
                output = '\n'.join(lines).strip()
                return output if output else "N/A"
            else:
                error_msg = result.stderr[:100] if result.stderr else f'Código de salida: {result.returncode}'
                if verbose:
                    print(f"  ⚠ Error en {hostname}: {error_msg}")
                return "N/A"
                
        except subprocess.TimeoutExpired:
            if verbose:
                print(f"  ⚠ Timeout en {hostname}")
            return "N/A"
        except Exception as e:
            if verbose:
                print(f"  ⚠ Excepción en {hostname}: {str(e)[:100]}")
            return "N/A"
    
    def run_remote_batch(self, hostnames, command, delay=0.5):
        """
        Ejecuta un comando en múltiples hosts
        
        Args:
            hostnames: Lista de hostnames
            command: Comando a ejecutar
            delay: Delay entre ejecuciones (segundos)
        
        Returns:
            dict: Diccionario con resultados por hostname
        """
        results = {}
        for hostname in hostnames:
            results[hostname] = self.run_remote(hostname, command)
            if delay > 0:
                import time
                time.sleep(delay)
        return results


def log_result(operation, hostname, success, details="", log_dir="data/logs"):
    """
    Guarda un log de operación
    
    Args:
        operation: Nombre de la operación (ej: "onedrive_fix")
        hostname: Hostname del equipo
        success: True si fue exitoso
        details: Detalles adicionales
        log_dir: Directorio de logs
    """
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{operation}_{datetime.now().strftime('%Y%m%d')}.log")
    
    status = "SUCCESS" if success else "FAILED"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {status} - {hostname} - {details}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)

