"""
Script analizador de Wi-Fi
Recolecta información detallada de conexión Wi-Fi para diagnóstico
"""
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.psexec_helper import PsExecHelper
from utils.common import save_report, clear_screen, load_config


def analyze_wifi(helper, hostname):
    """
    Analiza la conexión Wi-Fi del equipo remoto
    
    Args:
        helper: Instancia de PsExecHelper
        hostname: Hostname del equipo
    
    Returns:
        dict: Información de Wi-Fi recolectada
    """
    print(f"\n📡 Analizando Wi-Fi en {hostname}...")
    
    wifi_data = {
        "hostname": hostname,
        "timestamp": datetime.now().isoformat(),
        "connection": {},
        "signal": {},
        "network": {}
    }
    
    # Obtener información básica de la interfaz Wi-Fi
    print("  → Recolectando información de conexión...")
    interface_cmd = """
    $wlan = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -and ($_.InterfaceDescription -like '*Wireless*' -or $_.InterfaceDescription -like '*Wi-Fi*' -or $_.InterfaceDescription -like '*WLAN*') } | Select-Object -First 1;
    if ($wlan) {
        $wlanInfo = netsh wlan show interfaces name="$($wlan.Name)";
        $ssid = ($wlanInfo | Select-String 'SSID').ToString() -replace '.*SSID\\s*:\\s*', '';
        $bssid = ($wlanInfo | Select-String 'BSSID').ToString() -replace '.*BSSID\\s*:\\s*', '';
        $signal = ($wlanInfo | Select-String 'Signal').ToString() -replace '.*Signal\\s*:\\s*', '' -replace '%', '';
        $radio = ($wlanInfo | Select-String 'Radio type').ToString() -replace '.*Radio type\\s*:\\s*', '';
        $channel = ($wlanInfo | Select-String 'Channel').ToString() -replace '.*Channel\\s*:\\s*', '';
        $speed = ($wlanInfo | Select-String 'Receive rate|Transmit rate').ToString() -replace '.*rate\\s*:\\s*', '' -replace '\\s+Mbps', '';
        [PSCustomObject]@{
            SSID = $ssid.Trim();
            BSSID = $bssid.Trim();
            Signal = $signal.Trim();
            RadioType = $radio.Trim();
            Channel = $channel.Trim();
            Speed = $speed.Trim();
            InterfaceName = $wlan.Name
        } | ConvertTo-Json
    } else {
        'No Wi-Fi adapter found'
    }
    """
    
    result = helper.run_remote(hostname, interface_cmd)
    
    if result != "N/A" and "No Wi-Fi adapter" not in result:
        try:
            wifi_info = json.loads(result)
            wifi_data["connection"] = {
                "ssid": wifi_info.get("SSID", "N/A"),
                "bssid": wifi_info.get("BSSID", "N/A"),
                "interface": wifi_info.get("InterfaceName", "N/A")
            }
            wifi_data["signal"] = {
                "strength_percent": wifi_info.get("Signal", "N/A"),
                "rssi": calculate_rssi(wifi_info.get("Signal", "0")),
                "quality": classify_signal(wifi_info.get("Signal", "0"))
            }
            wifi_data["network"] = {
                "band": detect_band(wifi_info.get("RadioType", "")),
                "channel": wifi_info.get("Channel", "N/A"),
                "speed_mbps": wifi_info.get("Speed", "N/A")
            }
        except:
            wifi_data["connection"]["error"] = "Error parseando datos"
    else:
        wifi_data["connection"]["error"] = "Adaptador Wi-Fi no encontrado o no conectado"
    
    # Obtener información de red (IP, Gateway, DNS)
    print("  → Recolectando información de red...")
    network_cmd = """
    $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*vEthernet*' -and $_.IPAddress -notlike '169.254.*' } | Select-Object -First 1).IPAddress;
    $gateway = (Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -First 1).NextHop;
    $dns = (Get-DnsClientServerAddress -AddressFamily IPv4 | Select-Object -First 1).ServerAddresses -join ', ';
    [PSCustomObject]@{
        IP = $ip;
        Gateway = $gateway;
        DNS = $dns
    } | ConvertTo-Json
    """
    
    network_result = helper.run_remote(hostname, network_cmd)
    if network_result != "N/A":
        try:
            net_info = json.loads(network_result)
            wifi_data["network"].update({
                "ip": net_info.get("IP", "N/A"),
                "gateway": net_info.get("Gateway", "N/A"),
                "dns": net_info.get("DNS", "N/A")
            })
        except:
            pass
    
    # Test de conectividad
    print("  → Probando conectividad...")
    ping_cmd = """
    $targets = @('8.8.8.8', '1.1.1.1', 'google.com');
    $results = @();
    foreach ($target in $targets) {
        $ping = Test-Connection -ComputerName $target -Count 2 -Quiet;
        $results += [PSCustomObject]@{
            Target = $target;
            Success = $ping
        }
    }
    $results | ConvertTo-Json
    """
    
    ping_result = helper.run_remote(hostname, ping_cmd)
    if ping_result != "N/A":
        try:
            ping_data = json.loads(ping_result)
            wifi_data["connectivity"] = ping_data if isinstance(ping_data, list) else [ping_data]
        except:
            wifi_data["connectivity"] = []
    
    return wifi_data


def calculate_rssi(signal_percent):
    """Calcula RSSI aproximado desde porcentaje de señal"""
    try:
        percent = int(signal_percent)
        # RSSI típico va de -100 (peor) a 0 (mejor)
        # Asumimos que 100% = -30 dBm, 0% = -100 dBm
        rssi = -100 + (percent * 0.7)
        return round(rssi)
    except:
        return "N/A"


def classify_signal(signal_percent):
    """Clasifica la calidad de la señal"""
    try:
        percent = int(signal_percent)
        if percent >= 80:
            return "Excelente"
        elif percent >= 60:
            return "Buena"
        elif percent >= 40:
            return "Aceptable"
        elif percent >= 20:
            return "Débil"
        else:
            return "Muy débil"
    except:
        return "N/A"


def detect_band(radio_type):
    """Detecta la banda (2.4 GHz o 5 GHz) desde el tipo de radio"""
    radio_lower = radio_type.lower()
    if "802.11a" in radio_lower or "802.11ac" in radio_lower or "802.11ax" in radio_lower or "5" in radio_lower:
        return "5 GHz"
    elif "802.11b" in radio_lower or "802.11g" in radio_lower or "802.11n" in radio_lower:
        # 802.11n puede ser ambos, pero si no especifica, asumimos 2.4
        if "5" in radio_lower:
            return "5 GHz"
        return "2.4 GHz"
    else:
        return "Desconocido"


def main():
    """Función principal"""
    clear_screen()
    config = load_config()
    
    helper = PsExecHelper(
        psexec_path=config.get("psexec_path", "PsExec.exe"),
        remote_user=config.get("remote_user", "Administrador"),
        remote_pass=config.get("remote_pass", "")
    )
    
    print("=" * 60)
    print("📡 ANALIZADOR DE WI-FI")
    print("=" * 60)
    print("\n📦 Ingresá los inventarios (NBxxxxxx) separados por espacio")
    inv_list = input("Ej: NB100232 NB100549\n\nInventarios: ").strip().split()
    
    if not inv_list:
        print("❌ No se ingresaron inventarios")
        input("\nPresioná ENTER para salir...")
        return
    
    all_results = {}
    
    for inv in inv_list:
        result = analyze_wifi(helper, inv)
        all_results[inv] = result
        
        # Mostrar resumen
        if "error" not in result.get("connection", {}):
            ssid = result["connection"].get("ssid", "N/A")
            signal = result["signal"].get("strength_percent", "N/A")
            band = result["network"].get("band", "N/A")
            quality = result["signal"].get("quality", "N/A")
            print(f"\n✅ {inv}: SSID={ssid}, Señal={signal}% ({quality}), Banda={band}")
        else:
            print(f"\n⚠️  {inv}: {result['connection'].get('error', 'Error desconocido')}")
    
    # Guardar reporte
    report_path = save_report(all_results, "wifi_analysis")
    print(f"\n📄 Reporte guardado: {report_path}")
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    main()

