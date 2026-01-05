"""
Módulo de consola remota interactiva
Permite ejecutar comandos PowerShell en el equipo remoto
"""
import sys
import os
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.remote_executor import RemoteExecutor


def mostrar_ayuda():
    """Muestra comandos disponibles en la consola"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                   COMANDOS DISPONIBLES                        ║
╠══════════════════════════════════════════════════════════════╣
║  exit, salir    - Salir de la consola                        ║
║  cls, clear     - Limpiar pantalla                           ║
║  help, ayuda    - Mostrar esta ayuda                         ║
║  info           - Información del equipo remoto              ║
║  test           - Probar conexión                            ║
║  local:comando  - Ejecutar comando localmente                ║
╠══════════════════════════════════════════════════════════════╣
║  Cualquier otro comando se ejecuta en el equipo remoto       ║
║  usando Invoke-Command via WinRM                             ║
╚══════════════════════════════════════════════════════════════╝
""")


SCRIPT_INFO = '''
# Redirigir Write-Host a Write-Output (ejecución silenciosa)
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
$null = $true  # Silenciar definición de función

try {
    $systemInfo = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
    $osInfo = Get-WmiObject -Class Win32_OperatingSystem -ErrorAction SilentlyContinue

    Write-Host "Equipo   : $($systemInfo.Name)"
    Write-Host "Usuario  : $($env:USERNAME)"
    Write-Host "Modelo   : $($systemInfo.Model)"
    Write-Host "SO       : $($osInfo.Caption)"
    Write-Host "RAM      : $([math]::round($systemInfo.TotalPhysicalMemory / 1GB, 2)) GB"
} catch {
    Write-Output "❌ ERROR: $($_.Exception.Message)"
}
'''


def ejecutar(executor: RemoteExecutor, hostname: str):
    """
    Inicia la consola remota interactiva
    
    Args:
        executor: Instancia de RemoteExecutor
        hostname: Nombre del equipo remoto
    """
    print(f"\n🖥️ CONSOLA REMOTA - {hostname}")
    print("=" * 50)
    print("Escribí 'help' para ver comandos disponibles")
    print("Escribí 'exit' para salir")
    print()
    
    historial = []
    
    while True:
        try:
            # Prompt
            comando = input(f"PS {hostname}> ").strip()
            
            if not comando:
                continue
            
            # Guardar en historial
            historial.append(comando)
            
            # Comandos especiales
            cmd_lower = comando.lower()
            
            if cmd_lower in ['exit', 'salir', 'quit']:
                print("Saliendo de la consola remota...")
                break
            
            elif cmd_lower in ['cls', 'clear']:
                os.system('cls' if os.name == 'nt' else 'clear')
                continue
            
            elif cmd_lower in ['help', 'ayuda', '?']:
                mostrar_ayuda()
                continue
            
            elif cmd_lower == 'test':
                print("🔍 Probando conexión...")
                conn = executor.test_connection(hostname)
                if conn["ready"]:
                    print(f"✅ Conexión OK a {hostname}")
                else:
                    print(f"❌ Error de conexión")
                    for error in conn.get("errors", []):
                        print(f"   {error}")
                continue
            
            elif cmd_lower == 'info':
                result = executor.run_script_block(hostname, SCRIPT_INFO, timeout=30, verbose=False)
                if result:
                    print(result)
                else:
                    print("❌ Error obteniendo información")
                continue
            
            elif cmd_lower == 'historial':
                print("Historial de comandos:")
                for i, cmd in enumerate(historial[-20:], 1):
                    print(f"  {i}. {cmd}")
                continue
            
            elif comando.startswith('local:'):
                # Ejecutar comando local
                local_cmd = comando[6:].strip()
                if local_cmd:
                    print(f"Ejecutando localmente: {local_cmd}")
                    try:
                        result = subprocess.run(
                            local_cmd,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if result.stdout:
                            print(result.stdout)
                        if result.stderr:
                            print(result.stderr)
                    except subprocess.TimeoutExpired:
                        print("❌ Timeout")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                continue
            
            # Ejecutar comando remoto
            print(f"   🔄 Ejecutando comando...", end="", flush=True)
            result = executor.run_command(hostname, comando, timeout=120, verbose=False)
            
            if result:
                print(" ✅\n")
                print(result)
            else:
                print(" ❌\n")
                error = executor.get_last_error()
                if error:
                    print(f"❌ Error: {error}")
                else:
                    # Intentar obtener más información del resultado completo
                    full_result = executor.execute_command(hostname, comando, timeout=120, verbose=False)
                    if full_result.stderr:
                        print(f"⚠️  stderr: {full_result.stderr}")
                    if not full_result.success:
                        print("(Comando ejecutado pero sin salida o con error)")
                    else:
                        print("(Sin salida)")
            
        except KeyboardInterrupt:
            print("\n\nUse 'exit' para salir de la consola")
            continue
        except EOFError:
            break
    
    print()


def iniciar_consola_interactiva(hostname: str):
    """
    Inicia una sesión interactiva usando Enter-PSSession
    (Modo alternativo usando PowerShell nativo)
    
    Args:
        hostname: Nombre del equipo remoto
    """
    print(f"\n🖥️ CONSOLA INTERACTIVA - {hostname}")
    print("=" * 50)
    print("Iniciando sesión PowerShell remota...")
    print("Escribí 'Exit-PSSession' para salir")
    print()
    
    try:
        # Ejecutar PowerShell con Enter-PSSession
        subprocess.run([
            "powershell", "-NoProfile", "-NoExit", "-Command",
            f"Enter-PSSession -ComputerName {hostname}"
        ])
    except KeyboardInterrupt:
        print("\nSesión terminada")
    except Exception as e:
        print(f"❌ Error: {e}")


def ejecutar_menu(executor: RemoteExecutor, hostname: str):
    """
    Menú de opciones de consola remota
    
    Args:
        executor: Instancia de RemoteExecutor
        hostname: Nombre del equipo remoto
    """
    print(f"\n🖥️ CONSOLA REMOTA - {hostname}")
    print()
    print("1. Consola via Invoke-Command (recomendada)")
    print("2. Consola via Enter-PSSession (interactiva)")
    print("0. Cancelar")
    print()
    
    opcion = input("Seleccioná una opción: ").strip()
    
    if opcion == "1":
        ejecutar(executor, hostname)
    elif opcion == "2":
        iniciar_consola_interactiva(hostname)
    elif opcion == "0":
        return
    else:
        print("Opción inválida")
        input("\nPresioná ENTER para continuar...")


def main():
    """Función principal para ejecución standalone"""
    from utils.common import clear_screen
    
    clear_screen()
    print("=" * 60)
    print("🖥️ CONSOLA REMOTA")
    print("=" * 60)
    
    hostname = input("\nInventario: ").strip()
    if not hostname:
        print("❌ Debe ingresar un inventario")
        return
    
    executor = RemoteExecutor()
    
    print()
    conn = executor.test_connection(hostname)
    if not conn["ready"]:
        print(f"\n❌ No se pudo conectar a {hostname}")
        input("\nPresioná ENTER para salir...")
        return
    
    ejecutar(executor, hostname)


if __name__ == "__main__":
    main()

