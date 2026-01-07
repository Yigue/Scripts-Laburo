"""
Script de reparación automática de OneDrive
Resuelve problemas comunes de sincronización sin tocar físicamente el equipo
"""
import sys
import os
from datetime import datetime

from utils.remote_executor import RemoteExecutor
from utils.common import save_report, log_result

def ejecutar(executor: RemoteExecutor, hostname: str):
    print(f"\n🔧 Reparando OneDrive en {hostname}...")
    results = fix_onedrive(executor, hostname)
    
    if results["success"]:
        print(f"\n✅ {hostname}: Reparación completada ({results['success_rate']})")
    else:
        print(f"\n⚠️  {hostname}: Reparación parcial ({results['success_rate']})")
    
    return results

def fix_onedrive(executor, hostname):
    results = {
        "hostname": hostname,
        "timestamp": datetime.now().isoformat(),
        "steps": {}
    }

    def run(cmd, verbose=True):
        res = executor.run_command(hostname, cmd, verbose=verbose)
        return res if res is not None else "N/A"
    
    # Paso 1: Detener procesos OneDrive
    print("  → Deteniendo procesos OneDrive...")
    stop_cmd = "Get-Process -Name OneDrive -ErrorAction SilentlyContinue | Stop-Process -Force"
    stop_result = run(stop_cmd, verbose=False)
    results["steps"]["stop_processes"] = "OK" if stop_result != "N/A" else "SKIPPED"
    
    # Paso 2: Reset completo de OneDrive
    print("  → Ejecutando reset completo...")
    reset_cmd = "$onedrive = (Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders').{374DE290-123F-4565-9164-39C4925E467B}; if (Test-Path \"$env:LOCALAPPDATA\\Microsoft\\OneDrive\\onedrive.exe\") { & \"$env:LOCALAPPDATA\\Microsoft\\OneDrive\\onedrive.exe\" /reset } else { 'OneDrive no encontrado' }"
    reset_result = run(reset_cmd)
    results["steps"]["reset"] = "OK" if "OneDrive no encontrado" not in reset_result else "FAILED"
    
    # Paso 3: Limpiar cache corrupta
    print("  → Limpiando cache...")
    cache_cmd = "Remove-Item -Path \"$env:LOCALAPPDATA\\Microsoft\\OneDrive\\logs\" -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path \"$env:LOCALAPPDATA\\Microsoft\\OneDrive\\settings\" -Recurse -Force -ErrorAction SilentlyContinue; 'Cache limpiado'"
    cache_result = run(cache_cmd)
    results["steps"]["clear_cache"] = "OK" if "Cache limpiado" in cache_result else "FAILED"
    
    # Paso 4: Reiniciar servicio
    print("  → Reiniciando servicio...")
    service_cmd = "Restart-Service -Name 'OneSyncSvc' -ErrorAction SilentlyContinue; 'Servicio reiniciado'"
    service_result = run(service_cmd)
    results["steps"]["restart_service"] = "OK" if "Servicio reiniciado" in service_result else "SKIPPED"
    
    # Paso 5: Verificar archivos en conflicto
    print("  → Verificando conflictos...")
    conflict_cmd = "Get-ChildItem -Path \"$env:USERPROFILE\\OneDrive\" -Recurse -Filter '*conflict*' -ErrorAction SilentlyContinue | Select-Object -First 5 | ForEach-Object { $_.FullName }"
    conflicts = run(conflict_cmd)
    results["steps"]["check_conflicts"] = conflicts if conflicts != "N/A" else "Sin conflictos detectados"
    
    # Paso 6: Iniciar OneDrive nuevamente
    print("  → Iniciando OneDrive...")
    start_cmd = "Start-Process -FilePath \"$env:LOCALAPPDATA\\Microsoft\\OneDrive\\onedrive.exe\" -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2; 'OneDrive iniciado'"
    start_result = run(start_cmd)
    results["steps"]["start_onedrive"] = "OK" if "OneDrive iniciado" in start_result else "FAILED"
    
    # Determinar éxito general
    success_steps = sum(1 for v in results["steps"].values() if v == "OK")
    results["success"] = success_steps >= 4
    results["success_rate"] = f"{success_steps}/6"
    
    # Log
    log_result("onedrive_fix", hostname, results["success"], f"Rate: {results['success_rate']}")
    
    return results

if __name__ == "__main__":
    print("Este script debe ejecutarse desde el menú principal.")
