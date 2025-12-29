"""
Script para abrir una consola de comando remota usando WinRM o PsExec
Permite ejecutar comandos interactivamente sin que el equipo remoto abra ventanas
"""
import sys
import os
import subprocess
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.psexec_helper import PsExecHelper, test_ping
from utils.WinRM_Helper import WinRMHelper
from utils.common import clear_screen, load_config, get_credentials


def verificar_requisitos():
    """Verifica los requisitos del sistema"""
    print("\n🔍 Verificando requisitos...")
    
    requisitos = {
        "ping": False,
        "psexec": False,
        "powershell": False
    }
    
    # Verificar PowerShell
    try:
        result = subprocess.run(
            ["powershell", "-Command", "echo 'OK'"],
            capture_output=True,
            text=True,
            timeout=10
        )
        requisitos["powershell"] = "OK" in result.stdout
        print(f"  {'✅' if requisitos['powershell'] else '❌'} PowerShell")
    except Exception:
        print("  ❌ PowerShell no disponible")
    
    # Verificar ping
    try:
        subprocess.run(["ping", "-n", "1", "127.0.0.1"], capture_output=True, timeout=5)
        requisitos["ping"] = True
        print("  ✅ Comando ping")
    except Exception:
        print("  ❌ Comando ping no disponible")
    
    return requisitos


def verificar_conexion_completa(helper, hostname, metodo="psexec"):
    """
    Realiza verificación completa de conexión
    
    Args:
        helper: Instancia del helper
        hostname: Nombre del host
        metodo: "psexec" o "winrm"
    
    Returns:
        dict: Resultado de las verificaciones
    """
    print(f"\n{'=' * 60}")
    print(f"🔍 VERIFICANDO CONEXIÓN A {hostname}")
    print(f"{'=' * 60}")
    
    resultado = {
        "hostname": hostname,
        "metodo": metodo,
        "ping": False,
        "conectividad": False,
        "autenticacion": False,
        "comando_test": False,
        "errores": []
    }
    
    # 1. Ping
    print(f"\n1️⃣  Probando ping a {hostname}...")
    resultado["ping"] = test_ping(hostname, timeout=5)
    
    if resultado["ping"]:
        print(f"   ✅ El host responde al ping")
    else:
        print(f"   ❌ El host NO responde al ping")
        print(f"   ")
        print(f"   Posibles causas:")
        print(f"   • El hostname '{hostname}' puede ser incorrecto")
        print(f"   • El equipo está apagado o desconectado")
        print(f"   • El firewall bloquea ICMP (ping)")
        print(f"   • No hay conectividad de red")
        resultado["errores"].append("Host no responde al ping")
        
        continuar = input(f"\n   ¿Continuar de todos modos? (S/N): ").strip().upper()
        if continuar != "S":
            return resultado
    
    # 2. Verificar método de conexión
    if metodo == "psexec":
        print(f"\n2️⃣  Verificando PsExec...")
        
        psexec_ok, psexec_msg = helper.check_psexec()
        if psexec_ok:
            print(f"   ✅ {psexec_msg}")
        else:
            print(f"   ❌ {psexec_msg}")
            print(f"   ")
            print(f"   Para descargar PsExec:")
            print(f"   https://docs.microsoft.com/en-us/sysinternals/downloads/psexec")
            resultado["errores"].append("PsExec no encontrado")
            return resultado
        
        # 3. Probar conexión con PsExec
        print(f"\n3️⃣  Probando conexión PsExec a {hostname}...")
        print(f"   Usuario: {helper.remote_user}")
        print(f"   Contraseña: {'*' * len(helper.remote_pass) if helper.remote_pass else '(vacía)'}")
        
        conn_result = helper.test_connection(hostname, verbose=False)
        
        if conn_result["auth"]:
            resultado["conectividad"] = True
            resultado["autenticacion"] = True
            print(f"   ✅ Conexión establecida")
            print(f"   ✅ Autenticación correcta")
        else:
            for error in conn_result["errors"]:
                print(f"   ❌ {error}")
                resultado["errores"].append(error)
            
            if "Acceso denegado" in str(conn_result["errors"]) or "Access is denied" in str(conn_result["errors"]):
                print(f"   ")
                print(f"   Posibles soluciones:")
                print(f"   • Verificá que el usuario '{helper.remote_user}' exista")
                print(f"   • Verificá que la contraseña sea correcta")
                print(f"   • El usuario debe tener permisos de administrador")
            
            return resultado
        
        # 4. Probar comando de prueba
        print(f"\n4️⃣  Ejecutando comando de prueba...")
        test_output = helper.run_remote(hostname, "$env:COMPUTERNAME", timeout=15, verbose=False)
        
        if test_output != "N/A" and test_output:
            resultado["comando_test"] = True
            print(f"   ✅ Comando ejecutado correctamente")
            print(f"   📋 Nombre del equipo remoto: {test_output}")
        else:
            print(f"   ⚠️  El comando no devolvió resultado")
            resultado["errores"].append("Comando de prueba falló")
    
    else:  # WinRM
        print(f"\n2️⃣  Verificando WinRM...")
        
        # Probar conexión WinRM
        print(f"\n3️⃣  Probando conexión WinRM a {hostname}...")
        print(f"   Usuario: {helper.remote_user}")
        
        if helper.test_connection(hostname):
            resultado["conectividad"] = True
            resultado["autenticacion"] = True
            print(f"   ✅ Conexión WinRM establecida")
        else:
            print(f"   ❌ No se pudo conectar via WinRM")
            print(f"   ")
            print(f"   Posibles causas:")
            print(f"   • WinRM no está habilitado en el equipo remoto")
            print(f"   • Credenciales incorrectas")
            print(f"   • Firewall bloqueando puerto 5985/5986")
            resultado["errores"].append("Conexión WinRM fallida")
            return resultado
        
        # 4. Probar comando
        print(f"\n4️⃣  Ejecutando comando de prueba...")
        test_output = helper.run_remote(hostname, "$env:COMPUTERNAME", timeout=15, verbose=False)
        
        if test_output != "N/A" and test_output:
            resultado["comando_test"] = True
            print(f"   ✅ Comando ejecutado correctamente")
            print(f"   📋 Nombre del equipo remoto: {test_output}")
        else:
            print(f"   ⚠️  El comando no devolvió resultado")
    
    # Resumen
    print(f"\n{'=' * 60}")
    print(f"📊 RESUMEN DE VERIFICACIÓN")
    print(f"{'=' * 60}")
    
    checks = [
        ("Ping", resultado["ping"]),
        ("Conectividad", resultado["conectividad"]),
        ("Autenticación", resultado["autenticacion"]),
        ("Comando test", resultado["comando_test"])
    ]
    
    for nombre, estado in checks:
        print(f"   {'✅' if estado else '❌'} {nombre}")
    
    if resultado["errores"]:
        print(f"\n⚠️  Errores encontrados:")
        for error in resultado["errores"]:
            print(f"   • {error}")
    
    return resultado


def ejecutar_consola_interactiva(helper, hostname, metodo="psexec"):
    """
    Abre una consola remota interactiva
    
    Args:
        helper: Instancia del helper (PsExec o WinRM)
        hostname: Nombre del host remoto
        metodo: "psexec" o "winrm"
    """
    clear_screen()
    print(f"{'=' * 60}")
    print(f"🖥️  CONSOLA REMOTA - {hostname}")
    print(f"{'=' * 60}")
    print(f"Método: {metodo.upper()}")
    print(f"Usuario: {helper.remote_user}")
    print(f"{'=' * 60}")
    print()
    print("Comandos especiales:")
    print("  exit, salir, quit  → Cerrar consola")
    print("  cls, clear         → Limpiar pantalla")
    print("  historial          → Ver historial de comandos")
    print("  test               → Probar conexión")
    print("  info               → Info del sistema remoto")
    print(f"{'=' * 60}")
    
    historial = []
    errores_consecutivos = 0
    
    while True:
        try:
            comando = input(f"\n{hostname}> ").strip()
            
            if not comando:
                continue
            
            # Comandos especiales
            if comando.lower() in ['exit', 'salir', 'quit']:
                print("\n👋 Cerrando consola remota...")
                break
            
            if comando.lower() in ['cls', 'clear']:
                clear_screen()
                print(f"🖥️  Consola remota - {hostname} ({metodo.upper()})")
                continue
            
            if comando.lower() == 'historial':
                print("\n📜 Historial de comandos:")
                if historial:
                    for i, cmd in enumerate(historial, 1):
                        print(f"  {i}. {cmd}")
                else:
                    print("  (vacío)")
                continue
            
            if comando.lower() == 'test':
                print("\n🔍 Probando conexión...")
                if test_ping(hostname):
                    print("✅ Ping OK")
                else:
                    print("❌ Ping falló")
                
                test_result = helper.run_remote(hostname, "echo 'TEST_OK'", timeout=10, verbose=False)
                if test_result != "N/A" and "TEST_OK" in test_result:
                    print("✅ Ejecución remota OK")
                else:
                    print("❌ Ejecución remota falló")
                continue
            
            if comando.lower() == 'info':
                print("\n🔍 Obteniendo información del sistema...")
                info_cmd = """
                [PSCustomObject]@{
                    Hostname = $env:COMPUTERNAME
                    Usuario = $env:USERNAME
                    OS = (Get-WmiObject Win32_OperatingSystem).Caption
                    IP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*Loopback*' } | Select-Object -First 1).IPAddress
                } | Format-List
                """
                info_result = helper.run_remote(hostname, info_cmd, timeout=20, verbose=False)
                if info_result != "N/A":
                    print(f"\n{info_result}")
                else:
                    print("❌ No se pudo obtener información")
                continue
            
            # Agregar al historial
            historial.append(comando)
            
            # Ejecutar comando remoto
            print(f"\n⏳ Ejecutando...")
            resultado = helper.run_remote(hostname, comando, timeout=60, verbose=True)
            
            if resultado == "N/A":
                errores_consecutivos += 1
                print(f"❌ Error ejecutando comando")
                
                if errores_consecutivos >= 3:
                    print(f"\n⚠️  Múltiples errores consecutivos. ¿Verificar conexión? (S/N): ", end="")
                    if input().strip().upper() == "S":
                        verificar_conexion_completa(helper, hostname, metodo)
                    errores_consecutivos = 0
            else:
                errores_consecutivos = 0
                print(f"\n{resultado}")
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Ctrl+C detectado. Escribí 'exit' para salir.")
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Función principal"""
    clear_screen()
    config = load_config()
    
    print("=" * 60)
    print("🖥️  EJECUTAR CONSOLA REMOTA")
    print("=" * 60)
    
    # Verificar requisitos básicos
    requisitos = verificar_requisitos()
    
    if not requisitos["powershell"]:
        print("\n❌ PowerShell es requerido para esta herramienta")
        input("\nPresioná ENTER para salir...")
        return
    
    print("\n¿Qué método de conexión querés usar?")
    print("1. PsExec (recomendado para dominios)")
    print("2. WinRM (PowerShell Remoting)")
    
    metodo = input("\nOpción (1 o 2) [1]: ").strip() or "1"
    
    # Solicitar hostname
    hostname = input("\n📦 Hostname del equipo remoto (ej: NB036595): ").strip()
    if not hostname:
        print("❌ Debes ingresar un hostname")
        input("\nPresioná ENTER para salir...")
        return
    
    # Solicitar credenciales
    user, password = get_credentials()
    
    if not password:
        print("\n⚠️  Advertencia: La contraseña está vacía")
        print("   Esto puede causar errores de autenticación")
        continuar = input("   ¿Continuar? (S/N): ").strip().upper()
        if continuar != "S":
            return
    
    # Crear helper según método
    if metodo == "1":
        helper = PsExecHelper(
            psexec_path=config.get("psexec_path", "PsExec.exe"),
            remote_user=user,
            remote_pass=password
        )
        metodo_str = "psexec"
    else:
        helper = WinRMHelper(
            remote_user=user,
            remote_pass=password
        )
        metodo_str = "winrm"
    
    # Verificar conexión
    verificacion = verificar_conexion_completa(helper, hostname, metodo_str)
    
    if not verificacion["conectividad"]:
        print("\n❌ No se pudo establecer conexión")
        print("   Revisá los errores anteriores e intentá de nuevo")
        input("\nPresioná ENTER para salir...")
        return
    
    # Preguntar qué hacer
    print("\n¿Qué querés hacer?")
    print("1. Abrir consola interactiva")
    print("2. Ejecutar un solo comando")
    print("3. Salir")
    
    opcion = input("\nOpción: ").strip()
    
    if opcion == "1":
        ejecutar_consola_interactiva(helper, hostname, metodo_str)
    
    elif opcion == "2":
        comando = input("\nComando a ejecutar: ").strip()
        if comando:
            print(f"\n⏳ Ejecutando...")
            resultado = helper.run_remote(hostname, comando, timeout=60)
            
            if resultado == "N/A":
                print("\n❌ Error ejecutando comando")
            else:
                print(f"\n📄 Resultado:\n{resultado}")
    
    elif opcion == "3":
        print("\n👋 ¡Hasta luego!")
        return
    
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    main()
