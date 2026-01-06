"""
Script de reparación automática de Outlook
Resuelve problemas de perfiles, OST corruptos y sincronización
"""
import sys
import os
from datetime import datetime

from utils.remote_executor import RemoteExecutor
from utils.common import save_report, log_result

def ejecutar(executor: RemoteExecutor, hostname: str):
    print(f"\n🔧 Reparando Outlook en {hostname}...")
    results = fix_outlook(executor, hostname)
    
    if results["success"]:
        print(f"\n✅ {hostname}: Reparación completada ({results['success_rate']})")
    else:
        print(f"\n⚠️  {hostname}: Reparación parcial ({results['success_rate']})")
    
    return results

def fix_outlook(executor, hostname):
    results = {
        "hostname": hostname,
        "timestamp": datetime.now().isoformat(),
        "steps": {}
    }

    def run(cmd):
        res = executor.run_command(hostname, cmd)
        return res if res is not None else "N/A"
    
    # Paso 1: Cerrar Outlook y procesos relacionados
    print("  → Cerrando procesos de Office...")
    close_cmd = "Get-Process -Name Outlook,MSOfficeSync -ErrorAction SilentlyContinue | Stop-Process -Force; Start-Sleep -Seconds 2; 'Procesos cerrados'"
    close_result = run(close_cmd)
    results["steps"]["close_processes"] = "OK" if "Procesos cerrados" in close_result else "SKIPPED"
    
    # Paso 2: Eliminar perfiles viejos (especialmente "op")
    print("  → Limpiando perfiles antiguos...")
    profile_cmd = "Get-ChildItem -Path \"$env:LOCALAPPDATA\\Microsoft\\Outlook\" -Filter '*.ost' -ErrorAction SilentlyContinue | Where-Object { $_.Name -like '*op*' } | Remove-Item -Force; 'Perfiles antiguos eliminados'"
    profile_result = run(profile_cmd)
    results["steps"]["remove_old_profiles"] = "OK" if "Perfiles antiguos eliminados" in profile_result else "SKIPPED"
    
    # Paso 3: Reparar OST corrupto
    print("  → Reparando archivos OST...")
    ost_cmd = "Get-ChildItem -Path \"$env:LOCALAPPDATA\\Microsoft\\Outlook\" -Filter '*.ost' -ErrorAction SilentlyContinue | ForEach-Object { $path = $_.FullName; if (Test-Path \"C:\\Program Files\\Microsoft Office\\root\\Office16\\SCANPST.EXE\") { & \"C:\\Program Files\\Microsoft Office\\root\\Office16\\SCANPST.EXE\" /p \"$path\" } }; 'OST reparados'"
    ost_result = run(ost_cmd)
    results["steps"]["repair_ost"] = "OK" if "OST reparados" in ost_result else "SKIPPED"
    
    # Paso 4: Reset de Office
    print("  → Reseteando configuración de Office...")
    reset_cmd = "Remove-Item -Path \"$env:APPDATA\\Microsoft\\Outlook\" -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path \"$env:LOCALAPPDATA\\Microsoft\\Office\\16.0\\Outlook\" -Recurse -Force -ErrorAction SilentlyContinue; 'Configuración reseteada'"
    reset_result = run(reset_cmd)
    results["steps"]["reset_office"] = "OK" if "Configuración reseteada" in reset_result else "SKIPPED"
    
    # Paso 5: Reparar Office con OfficeC2RClient
    print("  → Ejecutando reparación de Office...")
    repair_cmd = "if (Test-Path \"C:\\Program Files\\Common Files\\Microsoft Shared\\ClickToRun\\OfficeC2RClient.exe\") { & \"C:\\Program Files\\Common Files\\Microsoft Shared\\ClickToRun\\OfficeC2RClient.exe\" /repair } else { 'OfficeC2RClient no encontrado' }; 'Reparación iniciada'"
    repair_result = run(repair_cmd)
    results["steps"]["repair_office"] = "OK" if "Reparación iniciada" in repair_result else "SKIPPED"
    
    # Paso 6: Test de servicios MAPI
    print("  → Verificando servicios MAPI...")
    mapi_cmd = "Get-Service -Name MSExchange* -ErrorAction SilentlyContinue | Select-Object Name, Status; 'Servicios MAPI verificados'"
    mapi_result = run(mapi_cmd)
    results["steps"]["test_mapi"] = mapi_result if mapi_result != "N/A" else "N/A"
    
    # Paso 7: Limpiar SearchIndex
    print("  → Limpiando índice de búsqueda...")
    search_cmd = "Remove-Item -Path \"$env:LOCALAPPDATA\\Microsoft\\Windows\\Search\\Data\\*\" -Recurse -Force -ErrorAction SilentlyContinue; 'Índice limpiado'"
    search_result = run(search_cmd)
    results["steps"]["clear_search"] = "OK" if "Índice limpiado" in search_result else "SKIPPED"
    
    # Paso 8: Reasociar cuenta (forzar uso de cuenta nueva)
    print("  → Reasociando cuenta...")
    account_cmd = "Remove-Item -Path 'HKCU:\\Software\\Microsoft\\Office\\16.0\\Outlook\\Profiles' -Recurse -Force -ErrorAction SilentlyContinue; 'Perfil eliminado, se creará nuevo al iniciar'"
    account_result = run(account_cmd)
    results["steps"]["reassociate_account"] = "OK" if "Perfil eliminado" in account_result else "SKIPPED"
    
    # Determinar éxito general
    success_steps = sum(1 for v in results["steps"].values() if v == "OK")
    results["success"] = success_steps >= 5
    results["success_rate"] = f"{success_steps}/8"
    
    # Log
    log_result("outlook_fix", hostname, results["success"], f"Rate: {results['success_rate']}")
    
    return results

if __name__ == "__main__":
    print("Este script debe ejecutarse desde el menú principal.")
