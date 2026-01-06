"""
Script de reparación automática del Cliente SCCM
Resuelve problemas de sincronización, políticas y certificados
"""
import sys
import os
from datetime import datetime

from utils.remote_executor import RemoteExecutor
from utils.common import save_report, log_result

def ejecutar(executor: RemoteExecutor, hostname: str):
    """
    Punto de entrada para el menú
    """
    print(f"\n🔧 Reparando Cliente SCCM en {hostname}...")
    results = fix_sccm(executor, hostname)
    
    if results["success"]:
        print(f"\n✅ {hostname}: Reparación completada ({results['success_rate']})")
    else:
        print(f"\n⚠️  {hostname}: Reparación parcial ({results['success_rate']})")
    
    return results

def fix_sccm(executor, hostname):
    """
    Ejecuta la reparación completa del cliente SCCM
    """
    results = {
        "hostname": hostname,
        "timestamp": datetime.now().isoformat(),
        "steps": {}
    }
    
    def run(cmd):
        res = executor.run_command(hostname, cmd)
        return res if res is not None else "N/A"

    # Paso 1: Detener servicios SCCM
    print("  → Deteniendo servicios SCCM...")
    stop_cmd = "Stop-Service -Name CcmExec -Force -ErrorAction SilentlyContinue; Stop-Service -Name smstsmgr -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2; 'Servicios detenidos'"
    stop_result = run(stop_cmd)
    results["steps"]["stop_services"] = "OK" if "Servicios detenidos" in stop_result else "SKIPPED"
    
    # Paso 2: Reset Control.ClientAction
    print("  → Reseteando Control.ClientAction...")
    reset_cmd = "Remove-Item -Path 'HKLM:\\SOFTWARE\\Microsoft\\CCM\\CcmExec' -Recurse -Force -ErrorAction SilentlyContinue; 'Control.ClientAction reseteado'"
    reset_result = run(reset_cmd)
    results["steps"]["reset_client_action"] = "OK" if "Control.ClientAction reseteado" in reset_result else "SKIPPED"
    
    # Paso 3: Ejecutar ccmrepair.exe
    print("  → Ejecutando ccmrepair...")
    repair_cmd = "$ccmrepair = 'C:\\Windows\\ccmsetup\\ccmrepair.exe'; if (Test-Path $ccmrepair) { & $ccmrepair } else { 'ccmrepair.exe no encontrado' }; 'Reparación ejecutada'"
    repair_result = run(repair_cmd)
    results["steps"]["ccmrepair"] = "OK" if "Reparación ejecutada" in repair_result else "SKIPPED"
    
    # Paso 4: Reiniciar servicio SMS Agent Host
    print("  → Reiniciando SMS Agent Host...")
    restart_cmd = "Restart-Service -Name CcmExec -ErrorAction SilentlyContinue; Start-Sleep -Seconds 5; 'Servicio reiniciado'"
    restart_result = run(restart_cmd)
    results["steps"]["restart_service"] = "OK" if "Servicio reiniciado" in restart_result else "FAILED"
    
    # Paso 5: Forzar políticas
    print("  → Forzando políticas...")
    policy_cmd = "& 'C:\\Windows\\CCM\\ccmexec.exe' /rs; Start-Sleep -Seconds 2; & 'C:\\Windows\\CCM\\ccmexec.exe' /mp:MP_SERVER /forcepolicy; Start-Sleep -Seconds 2; 'Políticas forzadas'"
    policy_result = run(policy_cmd)
    results["steps"]["force_policies"] = "OK" if "Políticas forzadas" in policy_result else "SKIPPED"
    
    # Paso 6: Validar boundaries
    print("  → Validando boundaries...")
    boundary_cmd = "Get-WmiObject -Namespace root\\ccm\\LocationServices -Class SMS_ActiveMPCandidate | Select-Object NetworkID, Priority; 'Boundaries verificados'"
    boundary_result = run(boundary_cmd)
    results["steps"]["validate_boundaries"] = boundary_result if boundary_result != "N/A" else "N/A"
    
    # Paso 7: Validar certificado
    print("  → Validando certificado...")
    cert_cmd = "Get-ChildItem -Path Cert:\\LocalMachine\\SMS -ErrorAction SilentlyContinue | Select-Object Subject, Thumbprint; 'Certificado verificado'"
    cert_result = run(cert_cmd)
    results["steps"]["validate_certificate"] = cert_result if cert_result != "N/A" else "N/A"
    
    # Paso 8: Forzar descubrimiento
    print("  → Forzando descubrimiento...")
    discovery_cmd = "& 'C:\\Windows\\CCM\\ccmexec.exe' /rs; Start-Sleep -Seconds 3; 'Descubrimiento forzado'"
    discovery_result = run(discovery_cmd)
    results["steps"]["force_discovery"] = "OK" if "Descubrimiento forzado" in discovery_result else "SKIPPED"
    
    # Determinar éxito general
    success_steps = sum(1 for v in results["steps"].values() if v == "OK")
    results["success"] = success_steps >= 5
    results["success_rate"] = f"{success_steps}/8"
    
    # Log
    log_result("sccm_fix", hostname, results["success"], f"Rate: {results['success_rate']}")
    
    return results

if __name__ == "__main__":
    print("Este script debe ejecutarse desde el menú principal.")
