"""
Script analizador de Wi-Fi
Recolecta información detallada de conexión Wi-Fi para diagnóstico
Funciona local y remotamente
"""
import sys
import os
import json
import subprocess
from datetime import datetime

from utils.remote_executor import RemoteExecutor
from utils.common import clear_screen, load_config, get_credentials


def ejecutar(executor: RemoteExecutor, hostname: str):
    result = analyze_wifi_remote(executor, hostname)
    print(f"\n✅ {hostname}: {show_wifi_summary(result)}")
    save_wifi_report({hostname: result}, "wifi_analysis")
    return result


def get_report_dir():
    """Obtiene el directorio de reportes (relativo al script)"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "data", "reports")


def save_wifi_report(data, filename_prefix="wifi_analysis"):
    """Guarda un reporte de Wi-Fi"""
    report_dir = get_report_dir()
    os.makedirs(report_dir, exist_ok=True)
    
    filepath = os.path.join(
        report_dir, 
        f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    return filepath


def analyze_wifi_local():
    """
    Analiza la conexión Wi-Fi del equipo local
    
    Returns:
        dict: Información de Wi-Fi recolectada
    """
    print("\n📡 Analizando Wi-Fi localmente...")
    
    hostname = os.environ.get('COMPUTERNAME', 'LOCAL')
    
    wifi_data = {
        "hostname": hostname,
        "timestamp": datetime.now().isoformat(),
        "connection": {},
        "signal": {},
        "network": {},
        "connectivity": []
    }
    
    # Obtener información de la interfaz Wi-Fi
    print("  → Recolectando información de conexión...")
    interface_cmd = """
    try {
        $wlanOutput = netsh wlan show interfaces
        
        # Parsear la salida línea por línea
        $ssid = ""
        $bssid = ""
        $signal = ""
        $radio = ""
        $channel = ""
        $speed = ""
        $state = ""
        
        foreach ($line in $wlanOutput -split "`n") {
            $line = $line.Trim()
            if ($line -match "^SSID\s*:\s*(.+)$" -and $line -notmatch "BSSID") {
                $ssid = $matches[1].Trim()
            }
            elseif ($line -match "^BSSID\s*:\s*(.+)$") {
                $bssid = $matches[1].Trim()
            }
            elseif ($line -match "^Se.+al\s*:\s*(\d+)") {
                $signal = $matches[1].Trim()
            }
            elseif ($line -match "^Signal\s*:\s*(\d+)") {
                $signal = $matches[1].Trim()
            }
            elseif ($line -match "^Radio type\s*:\s*(.+)$" -or $line -match "^Tipo de radio\s*:\s*(.+)$") {
                $radio = $matches[1].Trim()
            }
            elseif ($line -match "^Channel\s*:\s*(\d+)$" -or $line -match "^Canal\s*:\s*(\d+)$") {
                $channel = $matches[1].Trim()
            }
            elseif ($line -match "^Receive rate.*:\s*([\d.]+)") {
                $speed = $matches[1].Trim()
            }
            elseif ($line -match "^Velocidad de recepci.+n.*:\s*([\d.]+)") {
                $speed = $matches[1].Trim()
            }
            elseif ($line -match "^State\s*:\s*(.+)$" -or $line -match "^Estado\s*:\s*(.+)$") {
                $state = $matches[1].Trim()
            }
        }
        
        if ($ssid -or $state -eq "connected" -or $state -eq "conectado") {
            @{
                SSID = $ssid
                BSSID = $bssid
                Signal = $signal
                RadioType = $radio
                Channel = $channel
                Speed = $speed
                State = $state
            } | ConvertTo-Json
        } else {
            "NO_WIFI_CONNECTED"
        }
    } catch {
        "ERROR: $_"
    }
    """
    
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", interface_cmd],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout.strip()
        
        if "NO_WIFI_CONNECTED" in output:
            wifi_data["connection"]["error"] = "No hay conexión Wi-Fi activa"
        elif "ERROR:" in output:
            wifi_data["connection"]["error"] = output
        else:
            try:
                wifi_info = json.loads(output)
                wifi_data["connection"] = {
                    "ssid": wifi_info.get("SSID", "N/A"),
                    "bssid": wifi_info.get("BSSID", "N/A"),
                    "state": wifi_info.get("State", "N/A")
                }
                wifi_data["signal"] = {
                    "strength_percent": wifi_info.get("Signal", "N/A"),
                    "rssi": calculate_rssi(wifi_info.get("Signal", "0")),
                    "quality": classify_signal(wifi_info.get("Signal", "0"))
                }
                wifi_data["network"] = {
                    "band": detect_band(wifi_info.get("RadioType", "")),
                    "channel": wifi_info.get("Channel", "N/A"),
                    "speed_mbps": wifi_info.get("Speed", "N/A"),
                    "radio_type": wifi_info.get("RadioType", "N/A")
                }
            except json.JSONDecodeError as e:
                wifi_data["connection"]["error"] = f"Error parseando datos: {str(e)[:50]}"
    except Exception as e:
        wifi_data["connection"]["error"] = f"Error ejecutando comando: {str(e)[:50]}"
    
    # Obtener información de red (IP, Gateway, DNS)
    if "error" not in wifi_data["connection"]:
        print("  → Recolectando información de red...")
        network_cmd = """
        try {
            $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
                $_.InterfaceAlias -notlike '*vEthernet*' -and 
                $_.InterfaceAlias -notlike '*Loopback*' -and 
                $_.IPAddress -notlike '169.254.*' 
            } | Select-Object -First 1).IPAddress
            
            $gateway = (Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Select-Object -First 1).NextHop
            $dns = (Get-DnsClientServerAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.ServerAddresses } | Select-Object -First 1).ServerAddresses -join ', '
            
            @{
                IP = $ip
                Gateway = $gateway
                DNS = $dns
            } | ConvertTo-Json
        } catch {
            "ERROR: $_"
        }
        """
        
        try:
            net_result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", network_cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if net_result.returncode == 0 and "ERROR:" not in net_result.stdout:
                try:
                    net_info = json.loads(net_result.stdout.strip())
                    wifi_data["network"].update({
                        "ip": net_info.get("IP", "N/A"),
                        "gateway": net_info.get("Gateway", "N/A"),
                        "dns": net_info.get("DNS", "N/A")
                    })
                except:
                    pass
        except:
            pass
        
        # Test de conectividad
        print("  → Probando conectividad...")
        ping_cmd = """
        $targets = @('8.8.8.8', '1.1.1.1', 'google.com')
        $results = @()
        foreach ($target in $targets) {
            $ping = Test-Connection -ComputerName $target -Count 1 -Quiet -ErrorAction SilentlyContinue
            $results += @{
                Target = $target
                Success = $ping
            }
        }
        $results | ConvertTo-Json
        """
        
        try:
            ping_result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ping_cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if ping_result.returncode == 0:
                try:
                    ping_data = json.loads(ping_result.stdout.strip())
                    wifi_data["connectivity"] = ping_data if isinstance(ping_data, list) else [ping_data]
                except:
                    pass
        except:
            pass
    
    return wifi_data


def analyze_wifi_remote(executor: RemoteExecutor, hostname: str):
    """
    Analiza la conexión Wi-Fi del equipo remoto
    
    Args:
        executor: Instancia de RemoteExecutor
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
        "network": {},
        "connectivity": []
    }
    
    # Obtener información de la interfaz Wi-Fi
    print("  → Recolectando información de conexión...")
    interface_cmd = """
    try {
        $wlanOutput = netsh wlan show interfaces
        
        $ssid = ""
        $bssid = ""
        $signal = ""
        $radio = ""
        $channel = ""
        $speed = ""
        $state = ""
        
        foreach ($line in $wlanOutput -split "`n") {
            $line = $line.Trim()
            if ($line -match "^SSID\\s*:\\s*(.+)$" -and $line -notmatch "BSSID") {
                $ssid = $matches[1].Trim()
            }
            elseif ($line -match "^BSSID\\s*:\\s*(.+)$") {
                $bssid = $matches[1].Trim()
            }
            elseif ($line -match "^Se.+al\\s*:\\s*(\\d+)" -or $line -match "^Signal\\s*:\\s*(\\d+)") {
                $signal = $matches[1].Trim()
            }
            elseif ($line -match "^Radio type\\s*:\\s*(.+)$" -or $line -match "^Tipo de radio\\s*:\\s*(.+)$") {
                $radio = $matches[1].Trim()
            }
            elseif ($line -match "^Channel\\s*:\\s*(\\d+)$" -or $line -match "^Canal\\s*:\\s*(\\d+)$") {
                $channel = $matches[1].Trim()
            }
            elseif ($line -match "^Receive rate.*:\\s*([\\d.]+)" -or $line -match "^Velocidad de recepci.+n.*:\\s*([\\d.]+)") {
                $speed = $matches[1].Trim()
            }
            elseif ($line -match "^State\\s*:\\s*(.+)$" -or $line -match "^Estado\\s*:\\s*(.+)$") {
                $state = $matches[1].Trim()
            }
        }
        
        if ($ssid -or $state -eq "connected" -or $state -eq "conectado") {
            @{
                SSID = $ssid
                BSSID = $bssid
                Signal = $signal
                RadioType = $radio
                Channel = $channel
                Speed = $speed
                State = $state
            } | ConvertTo-Json
        } else {
            "NO_WIFI_CONNECTED"
        }
    } catch {
        "ERROR: $_"
    }
    """
    
    result = executor.run_command(hostname, interface_cmd)

    if result is None:
        result = "N/A"
    
    if result == "N/A":
        wifi_data["connection"]["error"] = "No se pudo conectar al equipo remoto"
    elif "NO_WIFI_CONNECTED" in result:
        wifi_data["connection"]["error"] = "No hay conexión Wi-Fi activa"
    elif "ERROR:" in result:
        wifi_data["connection"]["error"] = result
    else:
        try:
            wifi_info = json.loads(result)
            wifi_data["connection"] = {
                "ssid": wifi_info.get("SSID", "N/A"),
                "bssid": wifi_info.get("BSSID", "N/A"),
                "state": wifi_info.get("State", "N/A")
            }
            wifi_data["signal"] = {
                "strength_percent": wifi_info.get("Signal", "N/A"),
                "rssi": calculate_rssi(wifi_info.get("Signal", "0")),
                "quality": classify_signal(wifi_info.get("Signal", "0"))
            }
            wifi_data["network"] = {
                "band": detect_band(wifi_info.get("RadioType", "")),
                "channel": wifi_info.get("Channel", "N/A"),
                "speed_mbps": wifi_info.get("Speed", "N/A"),
                "radio_type": wifi_info.get("RadioType", "N/A")
            }
        except json.JSONDecodeError as e:
            wifi_data["connection"]["error"] = f"Error parseando datos: {str(e)[:50]}"
    
    # Obtener información de red
    if "error" not in wifi_data["connection"]:
        print("  → Recolectando información de red...")
        network_cmd = """
        try {
            $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
                $_.InterfaceAlias -notlike '*vEthernet*' -and 
                $_.IPAddress -notlike '169.254.*' 
            } | Select-Object -First 1).IPAddress
            
            $gateway = (Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Select-Object -First 1).NextHop
            $dns = (Get-DnsClientServerAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.ServerAddresses } | Select-Object -First 1).ServerAddresses -join ', '
            
            @{
                IP = $ip
                Gateway = $gateway
                DNS = $dns
            } | ConvertTo-Json
        } catch {
            "ERROR: $_"
        }
        """
        
        network_result = executor.run_command(hostname, network_cmd)
        if network_result is not None and "ERROR:" not in network_result:
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
        $targets = @('8.8.8.8', '1.1.1.1', 'google.com')
        $results = @()
        foreach ($target in $targets) {
            $ping = Test-Connection -ComputerName $target -Count 1 -Quiet -ErrorAction SilentlyContinue
            $results += @{
                Target = $target
                Success = $ping
            }
        }
        $results | ConvertTo-Json
        """
        
        ping_result = executor.run_command(hostname, ping_cmd)
        if ping_result is not None:
            try:
                ping_data = json.loads(ping_result)
                wifi_data["connectivity"] = ping_data if isinstance(ping_data, list) else [ping_data]
            except:
                pass
    
    return wifi_data


def calculate_rssi(signal_percent):
    """Calcula RSSI aproximado desde porcentaje de señal"""
    try:
        percent = int(str(signal_percent).replace("%", ""))
        # RSSI típico va de -100 (peor) a -30 (mejor)
        rssi = -100 + (percent * 0.7)
        return round(rssi)
    except (ValueError, TypeError):
        return "N/A"


def classify_signal(signal_percent):
    """Clasifica la calidad de la señal"""
    try:
        percent = int(str(signal_percent).replace("%", ""))
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
    except (ValueError, TypeError):
        return "N/A"


def detect_band(radio_type):
    """Detecta la banda (2.4 GHz o 5 GHz) desde el tipo de radio"""
    if not radio_type:
        return "Desconocido"
    
    radio_lower = radio_type.lower()
    
    # 5 GHz indicators
    if any(x in radio_lower for x in ["802.11ac", "802.11ax", "802.11a", "5ghz", "5 ghz"]):
        return "5 GHz"
    
    # 2.4 GHz indicators
    if any(x in radio_lower for x in ["802.11b", "802.11g", "2.4ghz", "2.4 ghz"]):
        return "2.4 GHz"
    
    # 802.11n puede ser ambos
    if "802.11n" in radio_lower:
        return "2.4/5 GHz (n)"
    
    return "Desconocido"


def show_wifi_summary(wifi_data):
    """Muestra resumen de los datos de Wi-Fi"""
    connection = wifi_data.get("connection", {})
    signal = wifi_data.get("signal", {})
    network = wifi_data.get("network", {})
    
    if "error" in connection:
        return f"⚠️  Error: {connection['error']}"
    
    ssid = connection.get("ssid", "N/A")
    strength = signal.get("strength_percent", "N/A")
    quality = signal.get("quality", "N/A")
    band = network.get("band", "N/A")
    
    return f"SSID={ssid}, Señal={strength}% ({quality}), Banda={band}"


if __name__ == "__main__":
    print("Este script debe ejecutarse desde el menú principal.")
