"""
Módulo ejecutor de comandos remotos usando WinRM (PowerShell Remoting)
Usa la sesión actual de administrador, sin necesidad de credenciales
"""
import subprocess
import os
import json
from datetime import datetime


class WinRMExecutor:
    """
    Ejecutor de comandos remotos usando WinRM (Invoke-Command)
    Usa la sesión actual de administrador, no requiere credenciales
    """
    
    def __init__(self):
        """Inicializa el ejecutor"""
        self.current_hostname = None
        self._last_error = None
    
    def test_ping(self, hostname, count=2, timeout=5):
        """
        Prueba conectividad básica con ping
        
        Args:
            hostname: Nombre del host
            count: Número de pings
            timeout: Timeout en segundos
        
        Returns:
            bool: True si responde al ping
        """
        try:
            result = subprocess.run(
                ["ping", "-n", str(count), "-w", str(timeout * 1000), hostname],
                capture_output=True,
                text=True,
                timeout=timeout + 5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def test_connection(self, hostname, verbose=True):
        """
        Prueba la conexión WinRM completa a un host
        
        Args:
            hostname: Nombre del host remoto
            verbose: Si True, muestra mensajes de progreso
        
        Returns:
            dict: Resultado de las pruebas
        """
        result = {
            "hostname": hostname,
            "ping": False,
            "winrm": False,
            "ready": False,
            "errors": []
        }
        
        # 1. Ping
        if verbose:
            print(f"🔍 Probando ping a {hostname}...")
        
        result["ping"] = self.test_ping(hostname)
        
        if not result["ping"]:
            result["errors"].append("El host no responde al ping")
            if verbose:
                print(f"   ❌ El host no responde al ping")
            return result
        
        if verbose:
            print(f"   ✅ Ping OK")
        
        # 2. Test WinRM con comando simple
        if verbose:
            print(f"🔍 Probando conexión WinRM...")
        
        test_cmd = f'Invoke-Command -ComputerName {hostname} -ScriptBlock {{ $env:COMPUTERNAME }} -ErrorAction Stop'
        
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", test_cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if proc.returncode == 0 and proc.stdout.strip():
                result["winrm"] = True
                result["ready"] = True
                result["remote_name"] = proc.stdout.strip()
                if verbose:
                    print(f"   ✅ WinRM OK (Equipo: {result['remote_name']})")
            else:
                error = proc.stderr.strip() if proc.stderr else "Error desconocido"
                result["errors"].append(f"WinRM falló: {error[:100]}")
                if verbose:
                    print(f"   ❌ WinRM falló")
                    if "Access is denied" in error or "Acceso denegado" in error:
                        print("      Verificá que WinRM esté habilitado en el equipo remoto")
                    elif "cannot find" in error.lower() or "no se puede encontrar" in error.lower():
                        print("      No se puede resolver el nombre del host")
        
        except subprocess.TimeoutExpired:
            result["errors"].append("Timeout de conexión WinRM")
            if verbose:
                print(f"   ❌ Timeout de conexión")
        except Exception as e:
            result["errors"].append(str(e))
            if verbose:
                print(f"   ❌ Error: {e}")
        
        return result
    
    def run_command(self, hostname, command, timeout=60, verbose=True):
        """
        Ejecuta un comando PowerShell en el host remoto
        
        Args:
            hostname: Nombre del host remoto
            command: Comando PowerShell a ejecutar
            timeout: Timeout en segundos
            verbose: Si True, muestra errores
        
        Returns:
            str: Salida del comando o None si falla
        """
        # Escapar comillas dobles en el comando
        escaped_command = command.replace('"', '\\"')
        
        ps_cmd = f'Invoke-Command -ComputerName {hostname} -ScriptBlock {{ {escaped_command} }}'
        
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                return output if output else "(Comando ejecutado sin salida)"
            else:
                self._last_error = result.stderr.strip() if result.stderr else f"Código: {result.returncode}"
                if verbose:
                    print(f"⚠ Error: {self._last_error[:100]}")
                return None
                
        except subprocess.TimeoutExpired:
            self._last_error = f"Timeout ({timeout}s)"
            if verbose:
                print(f"⚠ Timeout ejecutando comando")
            return None
        except Exception as e:
            self._last_error = str(e)
            if verbose:
                print(f"⚠ Error: {e}")
            return None
    
    def run_script_block(self, hostname, script_block, timeout=120, verbose=True):
        """
        Ejecuta un bloque de script PowerShell complejo en el host remoto
        
        Args:
            hostname: Nombre del host remoto
            script_block: Bloque de script PowerShell (puede ser multilinea)
            timeout: Timeout en segundos
            verbose: Si True, muestra errores
        
        Returns:
            str: Salida del script o None si falla
        """
        # Para scripts complejos, usar archivo temporal
        import tempfile
        
        # Crear script wrapper que ejecuta el bloque remotamente
        wrapper_script = f'''
$scriptBlock = {{
{script_block}
}}
Invoke-Command -ComputerName {hostname} -ScriptBlock $scriptBlock
'''
        
        try:
            # Crear archivo temporal con el script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as f:
                f.write(wrapper_script)
                temp_path = f.name
            
            # Ejecutar el script
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", temp_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Eliminar archivo temporal
            os.unlink(temp_path)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                return output if output else "(Script ejecutado sin salida)"
            else:
                self._last_error = result.stderr.strip() if result.stderr else f"Código: {result.returncode}"
                if verbose:
                    print(f"⚠ Error: {self._last_error[:100]}")
                return None
                
        except subprocess.TimeoutExpired:
            self._last_error = f"Timeout ({timeout}s)"
            if verbose:
                print(f"⚠ Timeout ejecutando script")
            # Limpiar archivo temporal
            try:
                os.unlink(temp_path)
            except:
                pass
            return None
        except Exception as e:
            self._last_error = str(e)
            if verbose:
                print(f"⚠ Error: {e}")
            return None
    
    def run_command_with_args(self, hostname, command, args, timeout=60, verbose=True):
        """
        Ejecuta un comando con argumentos pasados al ScriptBlock
        
        Args:
            hostname: Nombre del host remoto
            command: Comando PowerShell con $args o param()
            args: Lista de argumentos
            timeout: Timeout en segundos
            verbose: Si True, muestra errores
        
        Returns:
            str: Salida del comando o None si falla
        """
        # Formatear argumentos
        args_str = ','.join([f'"{arg}"' if isinstance(arg, str) else str(arg) for arg in args])
        
        ps_cmd = f'Invoke-Command -ComputerName {hostname} -ScriptBlock {{ {command} }} -ArgumentList {args_str}'
        
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                return output if output else "(Comando ejecutado sin salida)"
            else:
                self._last_error = result.stderr.strip()
                if verbose:
                    print(f"⚠ Error: {self._last_error[:100]}")
                return None
                
        except subprocess.TimeoutExpired:
            self._last_error = f"Timeout ({timeout}s)"
            if verbose:
                print(f"⚠ Timeout")
            return None
        except Exception as e:
            self._last_error = str(e)
            if verbose:
                print(f"⚠ Error: {e}")
            return None
    
    def copy_file_to_remote(self, hostname, local_path, remote_path, verbose=True):
        """
        Copia un archivo al host remoto usando rutas UNC
        
        Args:
            hostname: Nombre del host remoto
            local_path: Ruta del archivo local
            remote_path: Ruta destino (ej: C:\\temp\\archivo.exe)
            verbose: Si True, muestra progreso
        
        Returns:
            bool: True si la copia fue exitosa
        """
        if not os.path.exists(local_path):
            if verbose:
                print(f"❌ Archivo no encontrado: {local_path}")
            return False
        
        # Convertir ruta remota a UNC (C:\temp -> \\hostname\c$\temp)
        if remote_path[1] == ':':
            drive = remote_path[0].lower()
            path_rest = remote_path[2:].replace('/', '\\')
            unc_path = f"\\\\{hostname}\\{drive}${path_rest}"
        else:
            unc_path = remote_path
        
        try:
            import shutil
            # Crear directorio destino si no existe
            dest_dir = os.path.dirname(unc_path)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Copiar archivo
            shutil.copy2(local_path, unc_path)
            
            if verbose:
                print(f"✅ Archivo copiado a {unc_path}")
            return True
            
        except Exception as e:
            if verbose:
                print(f"❌ Error copiando archivo: {e}")
            return False
    
    def get_last_error(self):
        """Retorna el último error ocurrido"""
        return self._last_error
    
    def restart_computer(self, hostname, force=True, wait=False, verbose=True):
        """
        Reinicia el equipo remoto
        
        Args:
            hostname: Nombre del host
            force: Si True, fuerza el reinicio
            wait: Si True, espera a que el equipo vuelva a estar online
            verbose: Si True, muestra mensajes
        
        Returns:
            bool: True si se inició el reinicio
        """
        force_param = "-Force" if force else ""
        
        cmd = f"Restart-Computer -ComputerName {hostname} {force_param}"
        
        if verbose:
            print(f"🔄 Reiniciando {hostname}...")
        
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                if verbose:
                    print(f"✅ Comando de reinicio enviado")
                
                if wait:
                    if verbose:
                        print(f"⏳ Esperando a que {hostname} vuelva a estar online...")
                    
                    import time
                    # Esperar a que se apague
                    time.sleep(10)
                    
                    # Esperar a que vuelva
                    for _ in range(60):  # Máximo 10 minutos
                        time.sleep(10)
                        if self.test_ping(hostname, count=1, timeout=3):
                            # Esperar un poco más para que WinRM esté listo
                            time.sleep(20)
                            if self.test_connection(hostname, verbose=False)["ready"]:
                                if verbose:
                                    print(f"✅ {hostname} está online nuevamente")
                                return True
                    
                    if verbose:
                        print(f"⚠ Timeout esperando reinicio")
                    return False
                
                return True
            else:
                if verbose:
                    print(f"❌ Error: {result.stderr[:100]}")
                return False
                
        except Exception as e:
            if verbose:
                print(f"❌ Error: {e}")
            return False


def test_executor():
    """Función de prueba para el ejecutor"""
    from common import clear_screen
    
    clear_screen()
    print("=" * 60)
    print("🔧 TEST WINRM EXECUTOR")
    print("=" * 60)
    
    hostname = input("\nHostname del equipo remoto: ").strip()
    if not hostname:
        print("❌ Debe ingresar un hostname")
        return
    
    executor = WinRMExecutor()
    
    # Test conexión
    print("\n" + "=" * 40)
    result = executor.test_connection(hostname)
    
    if not result["ready"]:
        print("\n❌ No se pudo establecer conexión")
        for error in result["errors"]:
            print(f"   • {error}")
        return
    
    # Test comandos
    print("\n" + "=" * 40)
    print("Ejecutando comandos de prueba...")
    
    # Comando simple
    print("\n1. Nombre del equipo:")
    output = executor.run_command(hostname, "$env:COMPUTERNAME")
    print(f"   {output}")
    
    # Comando con más info
    print("\n2. Usuario actual:")
    output = executor.run_command(hostname, "$env:USERNAME")
    print(f"   {output}")
    
    # Script block
    print("\n3. Información del sistema:")
    script = '''
    $os = Get-WmiObject Win32_OperatingSystem
    "$($os.Caption) - Build $($os.BuildNumber)"
    '''
    output = executor.run_script_block(hostname, script)
    print(f"   {output}")
    
    print("\n✅ Test completado")
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    test_executor()

