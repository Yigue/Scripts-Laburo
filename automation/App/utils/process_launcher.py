"""
Módulo para lanzar operaciones en nuevas ventanas de consola
Permite ejecutar operaciones sin bloquear la consola principal
"""
import subprocess
import sys
import os

# Path base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def launch_menu_for_host(hostname: str) -> bool:
    """
    Lanza una instancia del menú principal para un hostname específico.
    Hereda los permisos del proceso actual (Admin).
    """
    try:
        main_script = os.path.join(BASE_DIR, "main.py")
        python_exe = sys.executable
        title = f"Soporte IT - {hostname}"
        
        # Comando para ir al directorio y ejecutar main con el hostname
        inner_command = f"Set-Location -Path '{BASE_DIR}'; & '{python_exe}' '{main_script}' --hostname '{hostname}'"
        
        if os.name == 'nt':
            # Simplemente abrimos una nueva consola PowerShell.
            # Al no usar -Verb RunAs, hereda el token de seguridad del padre (que ya es Admin).
            launch_args = [
                'powershell.exe',
                '-NoExit',
                '-Command',
                f"$host.UI.RawUI.WindowTitle = '{title}'; {inner_command}"
            ]
            subprocess.Popen(launch_args, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(
                ['python', main_script, '--hostname', hostname],
                start_new_session=True,
                cwd=BASE_DIR
            )
        
        return True
        
    except Exception as e:
        print(f"Error lanzando menú para {hostname}: {e}")
        return False
