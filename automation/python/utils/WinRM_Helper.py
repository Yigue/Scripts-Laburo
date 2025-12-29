"""
Módulo helper para ejecución remota usando WinRM (Windows Remote Management)
Alternativa a PsExec que usa el protocolo nativo de Windows
"""
import subprocess
import os
import json
from datetime import datetime


class WinRMHelper:
    """Clase helper para ejecutar comandos remotos usando WinRM (PowerShell Remoting)"""
    
    def __init__(self, remote_user="Administrador", remote_pass="", use_ssl=False):
        """
        Inicializa el helper de WinRM
        
        Args:
            remote_user: Usuario remoto para autenticación
            remote_pass: Contraseña remota
            use_ssl: Si usar HTTPS para la conexión
        """
        self.remote_user = remote_user
        self.remote_pass = remote_pass
        self.use_ssl = use_ssl
    
    def test_connection(self, hostname):
        """
        Prueba la conexión WinRM con un host
        
        Args:
            hostname: Nombre del host remoto
        
        Returns:
            bool: True si la conexión es exitosa
        """
        cmd = f"""
        $cred = New-Object System.Management.Automation.PSCredential("{self.remote_user}", (ConvertTo-SecureString "{self.remote_pass}" -AsPlainText -Force))
        try {{
            Test-WSMan -ComputerName {hostname} -Credential $cred -ErrorAction Stop
            "CONNECTION_OK"
        }} catch {{
            "CONNECTION_FAILED: $_"
        }}
        """
        
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            return "CONNECTION_OK" in result.stdout
        except Exception:
            return False
    
    def run_remote(self, hostname, command, timeout=60, verbose=True):
        """
        Ejecuta un comando PowerShell remoto usando Invoke-Command
        
        Args:
            hostname: Nombre del host remoto
            command: Comando PowerShell a ejecutar
            timeout: Timeout en segundos
            verbose: Si True, muestra errores en consola
        
        Returns:
            str: Salida del comando o "N/A" si falla
        """
        # Escapar comillas dobles en el comando
        escaped_command = command.replace('"', '\\"').replace("'", "''")
        
        ps_script = f"""
        $ErrorActionPreference = 'Stop'
        try {{
            $secPass = ConvertTo-SecureString "{self.remote_pass}" -AsPlainText -Force
            $cred = New-Object System.Management.Automation.PSCredential("{self.remote_user}", $secPass)
            
            $session = New-PSSession -ComputerName {hostname} -Credential $cred -ErrorAction Stop
            
            $result = Invoke-Command -Session $session -ScriptBlock {{
                {command}
            }}
            
            Remove-PSSession -Session $session
            
            $result
        }} catch {{
            "WINRM_ERROR: $_"
        }}
        """
        
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = result.stdout.strip()
            
            if "WINRM_ERROR:" in output:
                if verbose:
                    print(f"  ⚠ Error WinRM en {hostname}: {output}")
                return "N/A"
            
            return output if output else "N/A"
            
        except subprocess.TimeoutExpired:
            if verbose:
                print(f"  ⚠ Timeout en {hostname}")
            return "N/A"
        except Exception as e:
            if verbose:
                print(f"  ⚠ Excepción en {hostname}: {str(e)[:200]}")
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
    
    def copy_file_to_remote(self, hostname, local_path, remote_path, verbose=True):
        """
        Copia un archivo al host remoto usando WinRM
        
        Args:
            hostname: Nombre del host remoto
            local_path: Ruta del archivo local
            remote_path: Ruta destino en el host remoto
            verbose: Si True, muestra mensajes
        
        Returns:
            bool: True si la copia fue exitosa
        """
        if not os.path.isfile(local_path):
            if verbose:
                print(f"  ⚠ Archivo no encontrado: {local_path}")
            return False
        
        ps_script = f"""
        $ErrorActionPreference = 'Stop'
        try {{
            $secPass = ConvertTo-SecureString "{self.remote_pass}" -AsPlainText -Force
            $cred = New-Object System.Management.Automation.PSCredential("{self.remote_user}", $secPass)
            
            $session = New-PSSession -ComputerName {hostname} -Credential $cred
            
            Copy-Item -Path "{local_path}" -Destination "{remote_path}" -ToSession $session
            
            Remove-PSSession -Session $session
            "COPY_OK"
        }} catch {{
            "COPY_ERROR: $_"
        }}
        """
        
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return "COPY_OK" in result.stdout
        except Exception:
            return False
    
    def get_remote_info(self, hostname):
        """
        Obtiene información básica del host remoto
        
        Args:
            hostname: Nombre del host remoto
        
        Returns:
            dict: Información del host
        """
        cmd = """
        @{
            ComputerName = $env:COMPUTERNAME
            UserName = $env:USERNAME
            Domain = $env:USERDOMAIN
            OS = (Get-WmiObject Win32_OperatingSystem).Caption
            OSVersion = (Get-WmiObject Win32_OperatingSystem).Version
            LastBoot = (Get-WmiObject Win32_OperatingSystem).LastBootUpTime
        } | ConvertTo-Json
        """
        
        result = self.run_remote(hostname, cmd, verbose=False)
        
        if result != "N/A":
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"error": "Error parseando datos"}
        
        return {"error": "No se pudo conectar"}


def setup_winrm_local():
    """
    Configura WinRM en el equipo local para aceptar conexiones remotas
    REQUIERE: Ejecutar como Administrador
    """
    print("🔧 Configurando WinRM en equipo local...")
    print("   NOTA: Requiere ejecutar como Administrador")
    
    commands = [
        # Habilitar WinRM
        "Enable-PSRemoting -Force -SkipNetworkProfileCheck",
        # Configurar TrustedHosts (permitir cualquier host - para entornos de confianza)
        'Set-Item WSMan:\\localhost\\Client\\TrustedHosts -Value "*" -Force',
        # Configurar autenticación básica
        "Set-Item WSMan:\\localhost\\Service\\AllowUnencrypted -Value $true -Force",
        # Reiniciar servicio
        "Restart-Service WinRM"
    ]
    
    for cmd in commands:
        try:
            print(f"  → Ejecutando: {cmd[:50]}...")
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0 and result.stderr:
                print(f"    ⚠ {result.stderr[:100]}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print("✅ Configuración de WinRM completada")


def main():
    """Función principal para pruebas"""
    print("=" * 60)
    print("🔧 WINRM HELPER - TEST")
    print("=" * 60)
    
    print("\nOpciones:")
    print("1. Probar conexión a un host")
    print("2. Ejecutar comando remoto")
    print("3. Configurar WinRM local (Admin)")
    
    opcion = input("\nOpción: ").strip()
    
    if opcion == "1":
        hostname = input("Hostname: ").strip()
        user = input("Usuario [Administrador]: ").strip() or "Administrador"
        password = input("Contraseña: ").strip()
        
        helper = WinRMHelper(remote_user=user, remote_pass=password)
        print(f"\n🔍 Probando conexión a {hostname}...")
        
        if helper.test_connection(hostname):
            print(f"✅ Conexión exitosa a {hostname}")
            
            info = helper.get_remote_info(hostname)
            print(f"\n📊 Información del host:")
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            print(f"❌ No se pudo conectar a {hostname}")
    
    elif opcion == "2":
        hostname = input("Hostname: ").strip()
        user = input("Usuario [Administrador]: ").strip() or "Administrador"
        password = input("Contraseña: ").strip()
        command = input("Comando PowerShell: ").strip()
        
        helper = WinRMHelper(remote_user=user, remote_pass=password)
        print(f"\n🔧 Ejecutando en {hostname}...")
        
        result = helper.run_remote(hostname, command)
        print(f"\n📄 Resultado:\n{result}")
    
    elif opcion == "3":
        confirm = input("¿Ejecutar como Admin? (S/N): ").strip().upper()
        if confirm == "S":
            setup_winrm_local()
    
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    main()
