"""
Verificación rápida de espacio en disco C:
"""
import json
from utils.remote_executor import RemoteExecutor

def ejecutar(executor: RemoteExecutor, hostname: str):
    print(f"\n💾 Verificando disco C: en {hostname}...")
    result = check_disk(executor, hostname)

    if result["success"]:
        data = result["data"]
        free_gb = data.get("FreeGB", 0)
        total_gb = data.get("TotalGB", 0)
        percent = data.get("PercentFree", 0)

        prefix = "✅ "
        if percent < 10:
            prefix = "🔴 CRÍTICO: "
        elif percent < 20:
            prefix = "🟡 ALERTA: "

        print(f"\n{prefix}Disco C:")
        print(f"   Libre: {free_gb} GB ({percent}%)")
        print(f"   Total: {total_gb} GB")
    else:
        print(f"\n❌ {result.get('error')}")

    return result

def check_disk(executor, hostname):
    cmd = """
    $disk = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
    @{
        FreeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
        TotalGB = [math]::Round($disk.Size / 1GB, 2)
        PercentFree = [math]::Round(($disk.FreeSpace / $disk.Size) * 100, 2)
    } | ConvertTo-Json
    """
    res = executor.run_command(hostname, cmd)

    result = {"success": False, "hostname": hostname}

    if res:
        try:
            data = json.loads(res)
            result["success"] = True
            result["data"] = data
        except:
            result["error"] = "Error interpretando datos"
    else:
        result["error"] = "No se pudo obtener información del disco"

    return result
