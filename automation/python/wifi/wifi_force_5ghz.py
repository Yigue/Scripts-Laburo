"""
Script para forzar conexión a 5GHz
Funciona en Windows (remoto) y Android (requiere ADB)
"""
import sys
import os
import subprocess
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.psexec_helper import PsExecHelper
from utils.common import save_report, clear_screen, load_config


def force_5ghz_windows(helper, hostname, target_ssid=None):
    """
    Fuerza conexión a 5GHz en Windows remoto
    Usa múltiples métodos para maximizar la probabilidad de éxito
    
    Args:
        helper: Instancia de PsExecHelper
        hostname: Hostname del equipo
        target_ssid: SSID específico (opcional)
    
    Returns:
        dict: Resultado de la operación
    """
    print(f"\n🔧 Forzando conexión 5GHz en {hostname}...")
    results = {
        "hostname": hostname,
        "platform": "Windows",
        "timestamp": datetime.now().isoformat(),
        "steps": {}
    }
    
    # Paso 0: Obtener información actual
    print("  → Obteniendo información actual...")
    current_info_cmd = """
    $wlan = netsh wlan show interfaces;
    $ssid = ($wlan | Select-String 'SSID').ToString() -replace '.*SSID\\s*:\\s*', '';
    $radio = ($wlan | Select-String 'Radio type').ToString() -replace '.*Radio type\\s*:\\s*', '';
    $band = if ($radio -like '*5*' -or $radio -like '*802.11a*' -or $radio -like '*802.11ac*' -or $radio -like '*802.11ax*') { '5 GHz' } else { '2.4 GHz' };
    [PSCustomObject]@{
        CurrentSSID = $ssid.Trim();
        CurrentBand = $band;
        RadioType = $radio.Trim()
    } | ConvertTo-Json
    """
    current_info = helper.run_remote(hostname, current_info_cmd)
    
    if current_info != "N/A":
        try:
            current_data = json.loads(current_info)
            results["initial_band"] = current_data.get("CurrentBand", "Desconocido")
            results["initial_ssid"] = current_data.get("CurrentSSID", "N/A")
            if "5 GHz" in results["initial_band"]:
                print(f"  ✅ Ya está conectado a 5GHz ({results['initial_ssid']})")
                results["success"] = True
                results["steps"]["already_5ghz"] = "OK"
                return results
        except:
            pass
    
    # Si no se especifica SSID, usar el actual
    if not target_ssid and current_info != "N/A":
        try:
            current_data = json.loads(current_info)
            target_ssid = current_data.get("CurrentSSID", "").strip()
        except:
            pass
    
    # Paso 1: Obtener perfiles Wi-Fi y encontrar el SSID objetivo
    print("  → Analizando perfiles Wi-Fi...")
    if target_ssid:
        print(f"  → SSID objetivo: {target_ssid}")
        # Obtener información del perfil específico
        profile_info_cmd = f"""
        $profile = netsh wlan show profile name=\"{target_ssid}\" key=clear;
        $profile | Out-String;
        """
        profile_info = helper.run_remote(hostname, profile_info_cmd)
        results["steps"]["analyze_profile"] = "OK" if profile_info != "N/A" else "FAILED"
    
    # Paso 2: Configurar preferencia de banda en el registro (método más efectivo)
    print("  → Configurando preferencia de banda en registro...")
    registry_cmd = """
    $adapter = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like '*Wireless*' -or $_.InterfaceDescription -like '*Wi-Fi*' -or $_.InterfaceDescription -like '*WLAN*' } | Select-Object -First 1;
    if ($adapter) {
        $regPath = "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}";
        $adapters = Get-ChildItem -Path $regPath -ErrorAction SilentlyContinue;
        foreach ($ad in $adapters) {
            $driverDesc = (Get-ItemProperty -Path $ad.PSPath -Name "DriverDesc" -ErrorAction SilentlyContinue).DriverDesc;
            if ($driverDesc -like '*Wireless*' -or $driverDesc -like '*Wi-Fi*' -or $driverDesc -like '*WLAN*') {
                # Preferir 5GHz (valor 1 = prefer 5GHz, 0 = prefer 2.4GHz, 2 = no preference)
                Set-ItemProperty -Path $ad.PSPath -Name "PreferredBand" -Value 1 -ErrorAction SilentlyContinue;
                Set-ItemProperty -Path $ad.PSPath -Name "BandPreference" -Value 1 -ErrorAction SilentlyContinue;
            }
        }
        'Registro configurado'
    } else {
        'Adaptador no encontrado'
    }
    """
    registry_result = helper.run_remote(hostname, registry_cmd)
    results["steps"]["configure_registry"] = "OK" if "Registro configurado" in registry_result else "SKIPPED"
    
    # Paso 3: Desconectar Wi-Fi actual
    print("  → Desconectando Wi-Fi actual...")
    disconnect_cmd = "netsh wlan disconnect; Start-Sleep -Seconds 3; 'Desconectado'"
    disconnect_result = helper.run_remote(hostname, disconnect_cmd)
    results["steps"]["disconnect"] = "OK" if "Desconectado" in disconnect_result else "SKIPPED"
    
    # Paso 4: Si hay SSID objetivo, eliminar y recrear perfil (fuerza nueva conexión)
    if target_ssid:
        print(f"  → Eliminando perfil de {target_ssid} para forzar reconexión...")
        delete_cmd = f"netsh wlan delete profile name=\"{target_ssid}\" interface=*; Start-Sleep -Seconds 2; 'Perfil eliminado'"
        delete_result = helper.run_remote(hostname, delete_cmd)
        results["steps"]["delete_profile"] = "OK" if "Perfil eliminado" in delete_result else "SKIPPED"
        
        # Reconectar al SSID (Windows intentará conectarse automáticamente)
        print(f"  → Reconectando a {target_ssid}...")
        reconnect_cmd = f"netsh wlan connect name=\"{target_ssid}\"; Start-Sleep -Seconds 5; 'Reconectado'"
        reconnect_result = helper.run_remote(hostname, reconnect_cmd)
        results["steps"]["reconnect"] = "OK" if "Reconectado" in reconnect_result else "SKIPPED"
    else:
        # Si no hay SSID específico, reiniciar adaptador
        print("  → Reiniciando adaptador Wi-Fi...")
        adapter_cmd = """
        $adapter = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like '*Wireless*' -or $_.InterfaceDescription -like '*Wi-Fi*' } | Select-Object -First 1;
        if ($adapter) {
            Disable-NetAdapter -Name $adapter.Name -Confirm:$false;
            Start-Sleep -Seconds 3;
            Enable-NetAdapter -Name $adapter.Name -Confirm:$false;
            Start-Sleep -Seconds 5;
            'Adaptador reiniciado'
        } else {
            'Adaptador no encontrado'
        }
        """
        adapter_result = helper.run_remote(hostname, adapter_cmd)
        results["steps"]["restart_adapter"] = "OK" if "Adaptador reiniciado" in adapter_result else "SKIPPED"
    
    # Paso 5: Verificar conexión actual (esperar un poco más)
    print("  → Verificando conexión actual (esperando estabilización)...")
    time.sleep(3)  # Esperar en el script local también
    
    verify_cmd = """
    Start-Sleep -Seconds 2;
    $wlan = netsh wlan show interfaces;
    $radio = ($wlan | Select-String 'Radio type').ToString() -replace '.*Radio type\\s*:\\s*', '';
    $ssid = ($wlan | Select-String 'SSID').ToString() -replace '.*SSID\\s*:\\s*', '';
    $signal = ($wlan | Select-String 'Signal').ToString() -replace '.*Signal\\s*:\\s*', '' -replace '%', '';
    $channel = ($wlan | Select-String 'Channel').ToString() -replace '.*Channel\\s*:\\s*', '';
    [PSCustomObject]@{
        SSID = $ssid.Trim();
        RadioType = $radio.Trim();
        Band = if ($radio -like '*5*' -or $radio -like '*802.11a*' -or $radio -like '*802.11ac*' -or $radio -like '*802.11ax*') { '5 GHz' } else { '2.4 GHz' };
        Signal = $signal.Trim();
        Channel = $channel.Trim()
    } | ConvertTo-Json
    """
    verify_result = helper.run_remote(hostname, verify_cmd)
    
    if verify_result != "N/A":
        try:
            verify_data = json.loads(verify_result)
            results["steps"]["verify"] = verify_data
            results["current_band"] = verify_data.get("Band", "Desconocido")
            results["current_ssid"] = verify_data.get("SSID", "N/A")
            results["current_signal"] = verify_data.get("Signal", "N/A")
            results["current_channel"] = verify_data.get("Channel", "N/A")
            results["success"] = "5 GHz" in results["current_band"]
        except Exception as e:
            results["steps"]["verify"] = f"Error parseando: {str(e)[:50]}"
            results["success"] = False
    else:
        results["steps"]["verify"] = "FAILED"
        results["success"] = False
    
    return results


def force_5ghz_android(device_id, target_ssid=None):
    """
    Fuerza conexión a 5GHz en Android usando ADB
    
    Args:
        device_id: ID del dispositivo Android (obtenido con 'adb devices')
        target_ssid: SSID específico (opcional)
    
    Returns:
        dict: Resultado de la operación
    """
    print(f"\n🔧 Forzando conexión 5GHz en Android ({device_id})...")
    results = {
        "device_id": device_id,
        "platform": "Android",
        "timestamp": datetime.now().isoformat(),
        "steps": {}
    }
    
    # Verificar que ADB esté disponible
    try:
        subprocess.run(["adb", "version"], capture_output=True, check=True)
    except:
        results["steps"]["check_adb"] = "FAILED - ADB no encontrado"
        results["success"] = False
        return results
    
    results["steps"]["check_adb"] = "OK"
    
    # Paso 1: Desconectar Wi-Fi actual
    print("  → Desconectando Wi-Fi...")
    disconnect_cmd = ["adb", "-s", device_id, "shell", "svc", "wifi", "disable"]
    try:
        subprocess.run(disconnect_cmd, capture_output=True, timeout=10)
        results["steps"]["disconnect"] = "OK"
    except:
        results["steps"]["disconnect"] = "FAILED"
    
    # Esperar un momento
    import time
    time.sleep(2)
    
    # Paso 2: Reconectar Wi-Fi (Android intentará conectarse a la mejor señal disponible)
    print("  → Reconectando Wi-Fi...")
    reconnect_cmd = ["adb", "-s", device_id, "shell", "svc", "wifi", "enable"]
    try:
        subprocess.run(reconnect_cmd, capture_output=True, timeout=10)
        results["steps"]["reconnect"] = "OK"
        time.sleep(5)
    except:
        results["steps"]["reconnect"] = "FAILED"
    
    # Paso 3: Verificar conexión (requiere permisos root o usar comandos alternativos)
    print("  → Verificando conexión...")
    # Nota: Obtener información detallada de Wi-Fi en Android requiere root
    # Alternativa: usar comandos básicos disponibles
    verify_cmd = ["adb", "-s", device_id, "shell", "dumpsys", "wifi", "|", "grep", "mWifiInfo"]
    try:
        verify_output = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=10)
        results["steps"]["verify"] = verify_output.stdout[:200] if verify_output.returncode == 0 else "N/A"
    except:
        results["steps"]["verify"] = "SKIPPED - Requiere permisos adicionales"
    
    results["success"] = results["steps"].get("reconnect") == "OK"
    results["note"] = "Android requiere root para forzar banda específica. Este script solo reconecta Wi-Fi."
    
    return results


def main():
    """Función principal"""
    clear_screen()
    config = load_config()
    
    print("=" * 60)
    print("🔧 FORZAR CONEXIÓN A 5GHz")
    print("=" * 60)
    print("\nSeleccioná la plataforma:")
    print("1. Windows (remoto con PsExec)")
    print("2. Android (local con ADB)")
    
    choice = input("\nOpción (1 o 2): ").strip()
    
    if choice == "1":
        # Windows remoto
        helper = PsExecHelper(
            psexec_path=config.get("psexec_path", "PsExec.exe"),
            remote_user=config.get("remote_user", "Administrador"),
            remote_pass=config.get("remote_pass", "")
        )
        
        print("\n📦 Ingresá los inventarios (NBxxxxxx) separados por espacio")
        inv_list = input("Ej: NB100232 NB100549\n\nInventarios: ").strip().split()
        
        target_ssid = input("\nSSID específico (Enter para omitir): ").strip() or None
        
        if not inv_list:
            print("❌ No se ingresaron inventarios")
            input("\nPresioná ENTER para salir...")
            return
        
        all_results = {}
        
        for inv in inv_list:
            result = force_5ghz_windows(helper, inv, target_ssid)
            all_results[inv] = result
            
            if result.get("success"):
                print(f"\n✅ {inv}: Conectado a {result.get('current_ssid', 'N/A')} en {result.get('current_band', 'N/A')}")
            else:
                print(f"\n⚠️  {inv}: No se pudo forzar 5GHz (banda actual: {result.get('current_band', 'Desconocido')})")
        
        # Guardar reporte
        report_path = save_report(all_results, "wifi_force_5ghz")
        print(f"\n📄 Reporte guardado: {report_path}")
        
    elif choice == "2":
        # Android local
        print("\n📱 Listando dispositivos Android conectados...")
        try:
            devices_output = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10)
            print(devices_output.stdout)
            
            device_id = input("\nIngresá el Device ID (o Enter para usar el primero): ").strip()
            
            if not device_id:
                # Intentar obtener el primer dispositivo
                lines = devices_output.stdout.strip().split('\n')[1:]
                if lines:
                    device_id = lines[0].split('\t')[0]
                else:
                    print("❌ No se encontraron dispositivos")
                    input("\nPresioná ENTER para salir...")
                    return
            
            target_ssid = input("\nSSID específico (Enter para omitir): ").strip() or None
            
            result = force_5ghz_android(device_id, target_ssid)
            
            if result.get("success"):
                print(f"\n✅ Dispositivo {device_id}: Wi-Fi reconectado")
            else:
                print(f"\n⚠️  Dispositivo {device_id}: {result.get('note', 'Operación falló')}")
            
            # Guardar reporte
            report_path = save_report({device_id: result}, "wifi_force_5ghz_android")
            print(f"\n📄 Reporte guardado: {report_path}")
            
        except FileNotFoundError:
            print("❌ ADB no está instalado o no está en el PATH")
            print("   Instalá Android Platform Tools y agregalo al PATH")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("❌ Opción inválida")
    
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    main()

