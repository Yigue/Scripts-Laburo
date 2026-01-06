"""
Módulo para obtener un resumen rápido del estado del equipo remoto.
"""
from typing import Dict, Optional
import re

def get_initial_status(executor, hostname: str) -> Dict[str, str]:
    """
    Obtiene información crítica del equipo de forma rápida.
    
    Returns:
        Dict con: user, disk_free, disk_total, uptime
    """
    script = '''
    try {
        $cs = Get-CimInstance Win32_ComputerSystem -ErrorAction Stop
        $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
        $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'" -ErrorAction Stop
        
        $uptime = (Get-Date) - $os.LastBootUpTime
        $uptimeStr = "{0}d {1}h {2}m" -f $uptime.Days, $uptime.Hours, $uptime.Minutes
        
        $freeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
        $sizeGB = [math]::Round($disk.Size / 1GB, 2)
        $diskPerc = [math]::Round(($freeGB / $sizeGB) * 100, 1)
        
        Write-Output "USER:$($cs.UserName)"
        Write-Output "UPTIME:$uptimeStr"
        Write-Output "DISK:$freeGB GB libres de $sizeGB GB ($diskPerc%)"
    } catch {
        Write-Output "ERROR:$($_.Exception.Message)"
    }
    '''
    
    result = executor.run_script_block(hostname, script, silent=True, verbose=False)
    
    status = {
        "user": "Desconocido",
        "uptime": "Desconocido",
        "disk": "Desconocido"
    }
    
    if result:
        for line in result.splitlines():
            if line.startswith("USER:"):
                status["user"] = line.replace("USER:", "").strip() or "Nadie logueado"
            elif line.startswith("UPTIME:"):
                status["uptime"] = line.replace("UPTIME:", "").strip()
            elif line.startswith("DISK:"):
                status["disk"] = line.replace("DISK:", "").strip()
            elif line.startswith("ERROR:"):
                status["error"] = line.replace("ERROR:", "").strip()
                
    return status
