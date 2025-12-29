"""
Módulo helper para ejecución de playbooks de Ansible
Facilita la ejecución de tareas remotas en Windows usando Ansible + WinRM
"""
import subprocess
import os
import json
import tempfile
from datetime import datetime


class AnsibleHelper:
    """Clase helper para ejecutar playbooks y comandos ad-hoc de Ansible"""
    
    def __init__(self, inventory_path=None, remote_user="Administrador", remote_pass=""):
        """
        Inicializa el helper de Ansible
        
        Args:
            inventory_path: Ruta al archivo de inventario
            remote_user: Usuario remoto para autenticación
            remote_pass: Contraseña remota
        """
        self.inventory_path = inventory_path
        self.remote_user = remote_user
        self.remote_pass = remote_pass
        self._ansible_available = self._check_ansible()
    
    def _check_ansible(self):
        """Verifica si Ansible está instalado"""
        try:
            result = subprocess.run(
                ["ansible", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    @property
    def is_available(self):
        """Retorna True si Ansible está disponible"""
        return self._ansible_available
    
    def create_temp_inventory(self, hosts):
        """
        Crea un archivo de inventario temporal
        
        Args:
            hosts: Lista de hostnames o diccionario con configuración
        
        Returns:
            str: Ruta al archivo de inventario temporal
        """
        inventory_content = "[windows_hosts]\n"
        
        if isinstance(hosts, list):
            for host in hosts:
                inventory_content += f"{host}\n"
        elif isinstance(hosts, dict):
            for host, vars in hosts.items():
                vars_str = " ".join([f"{k}={v}" for k, v in vars.items()])
                inventory_content += f"{host} {vars_str}\n"
        
        # Agregar variables de grupo
        inventory_content += """
[windows_hosts:vars]
ansible_connection=winrm
ansible_winrm_transport=ntlm
ansible_winrm_server_cert_validation=ignore
"""
        inventory_content += f"ansible_user={self.remote_user}\n"
        inventory_content += f"ansible_password={self.remote_pass}\n"
        
        # Crear archivo temporal
        fd, temp_path = tempfile.mkstemp(suffix=".ini", prefix="ansible_inv_")
        with os.fdopen(fd, 'w') as f:
            f.write(inventory_content)
        
        return temp_path
    
    def run_playbook(self, playbook_path, hosts=None, extra_vars=None, verbose=False):
        """
        Ejecuta un playbook de Ansible
        
        Args:
            playbook_path: Ruta al archivo playbook .yml
            hosts: Lista de hosts (si no se usa inventory_path)
            extra_vars: Variables adicionales para el playbook
            verbose: Si True, muestra output completo
        
        Returns:
            dict: Resultado de la ejecución
        """
        if not self._ansible_available:
            return {
                "success": False,
                "error": "Ansible no está instalado. Instalá con: pip install ansible pywinrm"
            }
        
        if not os.path.isfile(playbook_path):
            return {
                "success": False,
                "error": f"Playbook no encontrado: {playbook_path}"
            }
        
        # Determinar inventario
        temp_inv = None
        if hosts:
            temp_inv = self.create_temp_inventory(hosts)
            inventory = temp_inv
        elif self.inventory_path:
            inventory = self.inventory_path
        else:
            return {
                "success": False,
                "error": "No se especificó inventario ni hosts"
            }
        
        # Construir comando
        cmd = [
            "ansible-playbook",
            "-i", inventory,
            playbook_path
        ]
        
        if extra_vars:
            vars_str = " ".join([f"{k}={v}" for k, v in extra_vars.items()])
            cmd.extend(["-e", vars_str])
        
        if verbose:
            cmd.append("-v")
        
        result = {
            "playbook": playbook_path,
            "timestamp": datetime.now().isoformat(),
            "success": False
        }
        
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
            result["returncode"] = proc.returncode
            result["success"] = proc.returncode == 0
            
            if verbose:
                print(proc.stdout)
                if proc.stderr:
                    print(proc.stderr)
            
        except subprocess.TimeoutExpired:
            result["error"] = "Timeout ejecutando playbook"
        except Exception as e:
            result["error"] = str(e)
        finally:
            # Limpiar inventario temporal
            if temp_inv and os.path.exists(temp_inv):
                os.remove(temp_inv)
        
        return result
    
    def run_adhoc(self, hosts, module, args=None, verbose=False):
        """
        Ejecuta un comando ad-hoc de Ansible
        
        Args:
            hosts: Lista de hosts
            module: Módulo de Ansible (ej: 'win_shell', 'win_ping')
            args: Argumentos para el módulo
            verbose: Si True, muestra output completo
        
        Returns:
            dict: Resultado de la ejecución
        """
        if not self._ansible_available:
            return {
                "success": False,
                "error": "Ansible no está instalado"
            }
        
        # Crear inventario temporal
        temp_inv = self.create_temp_inventory(hosts)
        
        # Construir comando
        cmd = [
            "ansible",
            "windows_hosts",
            "-i", temp_inv,
            "-m", module
        ]
        
        if args:
            cmd.extend(["-a", args])
        
        if verbose:
            cmd.append("-v")
        
        result = {
            "module": module,
            "hosts": hosts,
            "timestamp": datetime.now().isoformat(),
            "success": False
        }
        
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
            result["returncode"] = proc.returncode
            result["success"] = proc.returncode == 0
            
            if verbose:
                print(proc.stdout)
            
        except subprocess.TimeoutExpired:
            result["error"] = "Timeout"
        except Exception as e:
            result["error"] = str(e)
        finally:
            if os.path.exists(temp_inv):
                os.remove(temp_inv)
        
        return result
    
    def ping(self, hosts):
        """
        Prueba conectividad con hosts usando win_ping
        
        Args:
            hosts: Lista de hosts
        
        Returns:
            dict: Resultados por host
        """
        return self.run_adhoc(hosts, "win_ping")
    
    def run_powershell(self, hosts, command):
        """
        Ejecuta comando PowerShell en hosts remotos
        
        Args:
            hosts: Lista de hosts
            command: Comando PowerShell
        
        Returns:
            dict: Resultado de la ejecución
        """
        return self.run_adhoc(hosts, "win_shell", command)


def check_requirements():
    """Verifica los requisitos para usar Ansible con Windows"""
    print("🔍 Verificando requisitos de Ansible...")
    
    requirements = {
        "ansible": False,
        "pywinrm": False,
        "requests_ntlm": False
    }
    
    # Verificar Ansible
    try:
        result = subprocess.run(["ansible", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            requirements["ansible"] = True
            # Extraer versión
            version = result.stdout.split('\n')[0] if result.stdout else "Unknown"
            print(f"  ✅ Ansible: {version}")
    except FileNotFoundError:
        print("  ❌ Ansible: No instalado")
    
    # Verificar módulos Python
    try:
        import winrm
        requirements["pywinrm"] = True
        print(f"  ✅ pywinrm: Instalado")
    except ImportError:
        print("  ❌ pywinrm: No instalado")
    
    try:
        import requests_ntlm
        requirements["requests_ntlm"] = True
        print(f"  ✅ requests_ntlm: Instalado")
    except ImportError:
        print("  ❌ requests_ntlm: No instalado")
    
    # Resumen
    all_ok = all(requirements.values())
    
    if not all_ok:
        print("\n⚠️  Faltan dependencias. Para instalar:")
        print("   pip install ansible pywinrm requests-ntlm")
    
    return all_ok


def main():
    """Función principal para pruebas"""
    print("=" * 60)
    print("🔧 ANSIBLE HELPER - TEST")
    print("=" * 60)
    
    print("\nOpciones:")
    print("1. Verificar requisitos")
    print("2. Ping a hosts")
    print("3. Ejecutar comando PowerShell")
    print("4. Ejecutar playbook")
    
    opcion = input("\nOpción: ").strip()
    
    if opcion == "1":
        check_requirements()
    
    elif opcion == "2":
        if not check_requirements():
            input("\nPresioná ENTER para salir...")
            return
        
        hosts = input("\nHosts (separados por espacio): ").strip().split()
        user = input("Usuario [Administrador]: ").strip() or "Administrador"
        password = input("Contraseña: ").strip()
        
        helper = AnsibleHelper(remote_user=user, remote_pass=password)
        print(f"\n🔍 Probando conectividad...")
        
        result = helper.ping(hosts)
        print(f"\n📄 Resultado:\n{result.get('stdout', result.get('error', 'Error'))}")
    
    elif opcion == "3":
        if not check_requirements():
            input("\nPresioná ENTER para salir...")
            return
        
        hosts = input("\nHosts (separados por espacio): ").strip().split()
        user = input("Usuario [Administrador]: ").strip() or "Administrador"
        password = input("Contraseña: ").strip()
        command = input("Comando PowerShell: ").strip()
        
        helper = AnsibleHelper(remote_user=user, remote_pass=password)
        print(f"\n🔧 Ejecutando...")
        
        result = helper.run_powershell(hosts, command)
        print(f"\n📄 Resultado:\n{result.get('stdout', result.get('error', 'Error'))}")
    
    elif opcion == "4":
        if not check_requirements():
            input("\nPresioná ENTER para salir...")
            return
        
        playbook = input("\nRuta del playbook: ").strip()
        hosts = input("Hosts (separados por espacio): ").strip().split()
        user = input("Usuario [Administrador]: ").strip() or "Administrador"
        password = input("Contraseña: ").strip()
        
        helper = AnsibleHelper(remote_user=user, remote_pass=password)
        print(f"\n🔧 Ejecutando playbook...")
        
        result = helper.run_playbook(playbook, hosts=hosts, verbose=True)
        
        if result.get("success"):
            print("\n✅ Playbook ejecutado exitosamente")
        else:
            print(f"\n❌ Error: {result.get('error', 'Error desconocido')}")
    
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    main()
