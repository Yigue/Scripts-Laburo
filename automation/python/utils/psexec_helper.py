"""
Módulo helper para ejecución remota usando PsExec
Refactorizado desde Especificacioens.py para uso reutilizable
"""
import subprocess
import os
import shutil
from datetime import datetime


def find_psexec(psexec_path="PsExec.exe"):
    """
    Busca PsExec.exe en ubicaciones comunes
    
    Args:
        psexec_path: Ruta proporcionada por el usuario
    
    Returns:
        str: Ruta completa a PsExec.exe o None si no se encuentra
    """
    # Si ya es una ruta absoluta y existe, usarla
    if os.path.isabs(psexec_path) and os.path.isfile(psexec_path):
        return psexec_path
    
    # Si es relativa y existe en el directorio actual
    if os.path.isfile(psexec_path):
        return os.path.abspath(psexec_path)
    
    # Buscar en el PATH del sistema
    psexec_in_path = shutil.which("PsExec.exe") or shutil.which("psexec.exe") or shutil.which("PsExec64.exe")
    if psexec_in_path:
        return psexec_in_path
    
    # Buscar en ubicaciones comunes
    common_paths = [
        os.path.join(os.getcwd(), "PsExec.exe"),
        os.path.join(os.getcwd(), "psexec.exe"),
        os.path.join(os.getcwd(), "PsExec64.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "PsExec.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "psexec.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "PsExec64.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "PSTools", "PsExec.exe"),
        os.path.join(os.path.expanduser("~"), "Downloads", "PSTools", "PsExec64.exe"),
        "C:\\PSTools\\PsExec.exe",
        "C:\\PSTools\\PsExec64.exe",
        "C:\\PSTools\\psexec.exe",
        "C:\\Sysinternals\\PsExec.exe",
        "C:\\Sysinternals\\PsExec64.exe",
        "C:\\Tools\\PsExec.exe",
        "C:\\Tools\\PsExec64.exe",
        "C:\\Program Files\\Sysinternals\\PsExec.exe",
        "C:\\Windows\\System32\\PsExec.exe",
    ]
    
    for path in common_paths:
        if os.path.isfile(path):
            return os.path.abspath(path)
    
    return None


def test_ping(hostname, timeout=3):
    """
    Prueba conectividad básica con ping
    
    Args:
        hostname: Nombre del host
        timeout: Timeout en segundos
    
    Returns:
        bool: True si responde al ping
    """
    try:
        # Windows ping
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout * 1000), hostname],
            capture_output=True,
            text=True,
            timeout=timeout + 2
        )
        return result.returncode == 0
    except Exception:
        return False


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
        # Buscar PsExec automáticamente
        found_path = find_psexec(psexec_path)
        if found_path:
            self.psexec_path = found_path
            self._psexec_not_found = False
        else:
            # Si no se encuentra, usar la ruta proporcionada (fallará pero con mejor mensaje)
            self.psexec_path = psexec_path
            self._psexec_not_found = True
        
        self.remote_user = remote_user
        self.remote_pass = remote_pass
    
    def check_psexec(self):
        """
        Verifica que PsExec esté disponible
        
        Returns:
            tuple: (bool disponible, str mensaje)
        """
        if self._psexec_not_found or not os.path.isfile(self.psexec_path):
            return False, (
                f"PsExec.exe no encontrado.\n"
                f"   Buscado en: {self.psexec_path}\n"
                f"   Descargá de: https://docs.microsoft.com/en-us/sysinternals/downloads/psexec"
            )
        return True, f"PsExec encontrado: {self.psexec_path}"
    
    def test_connection(self, hostname, verbose=True):
        """
        Prueba la conexión a un host remoto
        
        Args:
            hostname: Nombre del host
            verbose: Si True, muestra mensajes
        
        Returns:
            dict: Resultado de las pruebas
        """
        result = {
            "hostname": hostname,
            "ping": False,
            "psexec": False,
            "auth": False,
            "errors": []
        }
        
        # 1. Verificar PsExec
        psexec_ok, psexec_msg = self.check_psexec()
        if not psexec_ok:
            result["errors"].append(psexec_msg)
            if verbose:
                print(f"❌ {psexec_msg}")
            return result
        
        if verbose:
            print(f"✅ PsExec: {self.psexec_path}")
        
        # 2. Ping
        if verbose:
            print(f"🔍 Probando ping a {hostname}...")
        
        result["ping"] = test_ping(hostname)
        
        if not result["ping"]:
            result["errors"].append("El host no responde al ping")
            if verbose:
                print(f"❌ El host {hostname} no responde al ping")
                print("   Verificá que:")
                print("   - El hostname sea correcto")
                print("   - El equipo esté encendido y conectado a la red")
                print("   - El firewall permita ICMP")
            return result
        
        if verbose:
            print(f"✅ Ping OK")
        
        # 3. Probar PsExec con comando simple
        if verbose:
            print(f"🔍 Probando conexión PsExec...")
        
        # Comando de prueba simple
        test_cmd = (
            f'"{self.psexec_path}" \\\\{hostname} -accepteula -nobanner '
            f'-u "{self.remote_user}" -p "{self.remote_pass}" '
            f'cmd /c "echo CONNECTION_OK"'
        )
        
        try:
            proc = subprocess.run(
                test_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = proc.stdout + proc.stderr
            
            if "CONNECTION_OK" in output:
                result["psexec"] = True
                result["auth"] = True
                if verbose:
                    print(f"✅ Conexión PsExec OK")
                    print(f"✅ Autenticación OK (usuario: {self.remote_user})")
            else:
                # Analizar errores
                if "Access is denied" in output or "Acceso denegado" in output:
                    result["errors"].append("Acceso denegado - credenciales incorrectas")
                    if verbose:
                        print(f"❌ Acceso denegado")
                        print("   Verificá usuario y contraseña")
                elif "could not find" in output.lower() or "no se encuentra" in output.lower():
                    result["errors"].append("No se puede resolver el nombre del host")
                    if verbose:
                        print(f"❌ No se puede resolver el hostname")
                elif "network path" in output.lower() or "ruta de red" in output.lower():
                    result["errors"].append("No se puede acceder a la ruta de red")
                    if verbose:
                        print(f"❌ No se puede acceder a la ruta de red")
                        print("   Verificá que el servicio 'Admin$' esté disponible")
                elif "RPC server" in output or "servidor RPC" in output:
                    result["errors"].append("El servidor RPC no está disponible")
                    if verbose:
                        print(f"❌ El servidor RPC no está disponible")
                        print("   El equipo puede estar apagado o tener firewall activo")
                else:
                    result["errors"].append(f"Error desconocido: {output[:200]}")
                    if verbose:
                        print(f"❌ Error: {output[:200]}")
        
        except subprocess.TimeoutExpired:
            result["errors"].append("Timeout de conexión")
            if verbose:
                print(f"❌ Timeout de conexión")
        except Exception as e:
            result["errors"].append(f"Excepción: {str(e)}")
            if verbose:
                print(f"❌ Error: {e}")
        
        return result
    
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
        # Verificar que PsExec existe
        if self._psexec_not_found or not os.path.isfile(self.psexec_path):
            error_msg = (
                f"❌ PsExec.exe no encontrado.\n"
                f"   Buscado en: {self.psexec_path}\n"
                f"   Soluciones:\n"
                f"   1. Descargá PsExec de: https://docs.microsoft.com/en-us/sysinternals/downloads/psexec\n"
                f"   2. Colocalo en el directorio del script o en el PATH\n"
                f"   3. Especificá la ruta completa en config.json"
            )
            if verbose:
                print(error_msg)
            return "N/A"
        
        # Escapar comillas dobles en el comando para PowerShell
        escaped_command = command.replace('"', '\\"')
        
        # Construir comando PsExec
        # -accepteula: Acepta EULA automáticamente
        # -nobanner: No muestra banner de copyright
        # -h: Ejecuta con token elevado (admin)
        cmd = (
            f'"{self.psexec_path}" \\\\{hostname} -accepteula -nobanner -h '
            f'-u "{self.remote_user}" -p "{self.remote_pass}" '
            f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{escaped_command}"'
        )
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Combinar stdout y stderr (PsExec a veces usa stderr para output normal)
            output = result.stdout.strip()
            stderr = result.stderr.strip()
            
            # Filtrar líneas de PsExec del stderr
            if stderr:
                stderr_lines = [
                    line for line in stderr.split('\n')
                    if not any(x in line.lower() for x in ['psexec', 'sysinternals', 'connecting', 'starting', 'error code'])
                ]
                if stderr_lines:
                    output = output + '\n' + '\n'.join(stderr_lines)
            
            if result.returncode == 0 or output:
                # Limpiar líneas de PsExec
                lines = []
                for line in output.split('\n'):
                    line = line.strip()
                    if line and not line.startswith(hostname) and 'PsExec' not in line:
                        lines.append(line)
                
                output = '\n'.join(lines).strip()
                return output if output else "(Comando ejecutado sin salida)"
            else:
                error_msg = result.stderr[:200] if result.stderr else f'Código de salida: {result.returncode}'
                
                # Detectar errores comunes
                if "Access is denied" in error_msg or "Acceso denegado" in error_msg:
                    error_msg = "Acceso denegado - verificá credenciales"
                elif "could not start" in error_msg.lower():
                    error_msg = "No se pudo iniciar el proceso remoto"
                
                if verbose:
                    print(f"  ⚠ Error en {hostname}: {error_msg}")
                return "N/A"
                
        except subprocess.TimeoutExpired:
            if verbose:
                print(f"  ⚠ Timeout en {hostname} (>{timeout}s)")
            return "N/A"
        except Exception as e:
            if verbose:
                print(f"  ⚠ Excepción en {hostname}: {str(e)[:200]}")
            return "N/A"
    
    def run_cmd(self, hostname, command, timeout=30, verbose=True):
        """
        Ejecuta un comando CMD (no PowerShell) remoto usando PsExec
        
        Args:
            hostname: Nombre del host remoto
            command: Comando CMD a ejecutar
            timeout: Timeout en segundos
            verbose: Si True, muestra errores
        
        Returns:
            str: Salida del comando o "N/A" si falla
        """
        if self._psexec_not_found or not os.path.isfile(self.psexec_path):
            if verbose:
                print(f"❌ PsExec.exe no encontrado")
            return "N/A"
        
        cmd = (
            f'"{self.psexec_path}" \\\\{hostname} -accepteula -nobanner '
            f'-u "{self.remote_user}" -p "{self.remote_pass}" '
            f'cmd /c "{command}"'
        )
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = result.stdout.strip()
            if output:
                return output
            elif result.returncode == 0:
                return "(Comando ejecutado sin salida)"
            else:
                if verbose:
                    print(f"  ⚠ Error en {hostname}: código {result.returncode}")
                return "N/A"
                
        except subprocess.TimeoutExpired:
            if verbose:
                print(f"  ⚠ Timeout en {hostname}")
            return "N/A"
        except Exception as e:
            if verbose:
                print(f"  ⚠ Error en {hostname}: {e}")
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
        import time
        results = {}
        for hostname in hostnames:
            results[hostname] = self.run_remote(hostname, command)
            if delay > 0:
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
