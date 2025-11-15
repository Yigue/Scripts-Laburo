import subprocess
import json
import os
import time

PSEXEC_PATH = "PsExec.exe"
REMOTE_USER = "Administrador"   # Cambiar si usás LAPS
REMOTE_PASS = ""                # Si usas LAPS podés pedirlo por input

def clear():
    os.system("cls")

def run_remote(inv, command):
    # Escapar comillas dobles en el comando para PowerShell
    escaped_command = command.replace('"', '\\"')
    cmd = (
        f'{PSEXEC_PATH} \\\\{inv} -u "{REMOTE_USER}" -p "{REMOTE_PASS}" '
        f'powershell -NoProfile -Command "{escaped_command}"'
    )
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            # Limpiar líneas de PsExec (líneas que empiezan con el nombre del host)
            lines = [line for line in output.split('\n') if line.strip() and not line.strip().startswith(inv)]
            output = '\n'.join(lines).strip()
            return output if output else "N/A"
        else:
            print(f"  ⚠ Error en {inv}: {result.stderr[:100] if result.stderr else 'Código de salida: ' + str(result.returncode)}")
            return "N/A"
    except subprocess.TimeoutExpired:
        print(f"  ⚠ Timeout en {inv}")
        return "N/A"
    except Exception as e:
        print(f"  ⚠ Excepción en {inv}: {str(e)[:100]}")
        return "N/A"

def get_data_remote(inv):
    data = {}

    print(f"📡 Recolectando información de {inv}...")

    # CPU - tomar el primero si hay múltiples
    cpu_cmd = "(Get-CimInstance Win32_Processor | Select-Object -First 1).Name"
    data["cpu"] = run_remote(inv, cpu_cmd)
    
    # RAM - formatear como número con 2 decimales
    ram_cmd = "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)"
    data["ram_gb"] = run_remote(inv, ram_cmd)
    
    # GPU - tomar el primero si hay múltiples
    gpu_cmd = "(Get-CimInstance Win32_VideoController | Where-Object {$_.Name -notlike '*Basic*' -and $_.Name -notlike '*Standard*'} | Select-Object -First 1).Name"
    gpu_result = run_remote(inv, gpu_cmd)
    if gpu_result == "N/A":
        # Si no encuentra, tomar cualquier GPU
        gpu_cmd = "(Get-CimInstance Win32_VideoController | Select-Object -First 1).Name"
        data["gpu"] = run_remote(inv, gpu_cmd)
    else:
        data["gpu"] = gpu_result
    
    data["manufacturer"] = run_remote(inv, "(Get-CimInstance Win32_ComputerSystem).Manufacturer")
    data["model"] = run_remote(inv, "(Get-CimInstance Win32_ComputerSystem).Model")
    data["os"] = run_remote(inv, "(Get-CimInstance Win32_OperatingSystem).Caption")
    data["os_build"] = run_remote(inv, "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion').ReleaseId")

    # Batería - puede no existir en equipos de escritorio
    battery_cmd = "$bat = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue; if ($bat) { $bat.EstimatedChargeRemaining } else { 'N/A' }"
    data["battery_percent"] = run_remote(inv, battery_cmd)

    # RED
    # IP - tomar la primera IP que no sea virtual
    ip_cmd = "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike '*vEthernet*' -and $_.IPAddress -notlike '169.254.*'} | Select-Object -First 1).IPAddress"
    data["network"] = {
        "ip": run_remote(inv, ip_cmd),
        # Gateway - tomar el primero
        "gateway": run_remote(inv, "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -First 1).NextHop"),
        # DNS - convertir array a string separado por comas
        "dns": run_remote(inv, "(Get-DnsClientServerAddress -AddressFamily IPv4 | Select-Object -First 1).ServerAddresses -join ', '"),
        # SSID - extraer solo el valor
        "ssid": run_remote(inv, "$wlan = netsh wlan show interfaces; if ($wlan) { ($wlan | Select-String 'SSID' | Select-Object -First 1) -replace '.*SSID\\s*:\\s*', '' } else { 'N/A' }")
    }

    return data


def main():
    clear()
    print("📦 INGRESÁ INVENTARIOS (NBxxxxxx) SEPARADOS POR ESPACIO")
    inv_list = input("Ej: NB100232 NB100549 NB036608\n\nInventarios: ").split()

    results = {}

    for inv in inv_list:
        results[inv] = get_data_remote(inv)
        time.sleep(0.5)

    with open("inventario_psexec.json", "w") as f:
        json.dump(results, f, indent=4)

    print("\n✔ Archivo generado: inventario_psexec.json")
    input("Presioná ENTER para salir...")

if __name__ == "__main__":
    main()
