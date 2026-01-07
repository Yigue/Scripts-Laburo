"""
Reporte de salud de batería para Notebooks
"""
import json
from utils.remote_executor import RemoteExecutor

def ejecutar(executor: RemoteExecutor, hostname: str):
    print(f"\n🔋 Analizando batería en {hostname}...")
    result = check_battery(executor, hostname)

    if result["success"]:
        print(f"\n✅ Batería detectada:")
        data = result.get("data", {})
        if isinstance(data, list):
            data = data[0] # Tomar la primera batería si hay varias

        print(f"   Nivel de carga: {data.get('EstimatedChargeRemaining', 'N/A')}%")
        print(f"   Estado: {translate_status(data.get('BatteryStatus'))}")
    else:
        print(f"\n⚠️  {result.get('error')}")

    return result

def check_battery(executor, hostname):
    # BatteryStatus: 1 (Discharging), 2 (The system has access to AC so no battery is being discharged),
    # 3 (Fully Charged), 4 (Low), 5 (Critical), 6 (Charging), 7 (Charging and High), 8 (Charging and Low),
    # 9 (Charging and Critical), 10 (Undefined), 11 (Partially Charged)
    cmd = "Get-WmiObject -Class Win32_Battery | Select-Object EstimatedChargeRemaining, BatteryStatus, DesignCapacity, FullChargeCapacity | ConvertTo-Json"
    res = executor.run_command(hostname, cmd)

    result = {"success": False, "hostname": hostname}

    if res and "Win32_Battery" not in res: # Check if output is not empty/error
        try:
            data = json.loads(res)
            result["success"] = True
            result["data"] = data
        except json.JSONDecodeError:
            result["error"] = "No se pudo interpretar la respuesta del equipo (posiblemente sin batería o error de formato)"
            result["raw"] = res
    else:
        result["error"] = "No se detectó batería o falló la conexión"

    return result

def translate_status(status_code):
    statuses = {
        1: "Descargando",
        2: "Conectado (AC)",
        3: "Carga Completa",
        4: "Baja",
        5: "Crítica",
        6: "Cargando",
        7: "Cargando (Alta)",
        8: "Cargando (Baja)",
        9: "Cargando (Crítica)"
    }
    return statuses.get(status_code, f"Desconocido ({status_code})")
