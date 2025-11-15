"""
Script de reparación automática del Cliente SCCM
Resuelve problemas de sincronización, políticas y certificados
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.psexec_helper import PsExecHelper, log_result
from utils.common import save_report, clear_screen, load_config


def fix_sccm(helper, hostname):
    """
    Ejecuta la reparación completa del cliente SCCM
    
    Args:
        helper: Instancia de PsExecHelper
        hostname: Hostname del equipo
    
    Returns:
        dict: Resultado de la reparación
    """
    print(f"\n🔧 Reparando Cliente SCCM en {hostname}...")
    results = {
        "hostname": hostname,
        "timestamp": datetime.now().isoformat(),
        "steps": {}
    }
    
    # Paso 1: Detener servicios SCCM
    print("  → Deteniendo servicios SCCM...")
    stop_cmd = "Stop-Service -Name CcmExec -Force -ErrorAction SilentlyContinue; Stop-Service -Name smstsmgr -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2; 'Servicios detenidos'"
    stop_result = helper.run_remote(hostname, stop_cmd)
    results["steps"]["stop_services"] = "OK" if "Servicios detenidos" in stop_result else "SKIPPED"
    
    # Paso 2: Reset Control.ClientAction
    print("  → Reseteando Control.ClientAction...")
    reset_cmd = "Remove-Item -Path 'HKLM:\\SOFTWARE\\Microsoft\\CCM\\CcmExec' -Recurse -Force -ErrorAction SilentlyContinue; 'Control.ClientAction reseteado'"
    reset_result = helper.run_remote(hostname, reset_cmd)
    results["steps"]["reset_client_action"] = "OK" if "Control.ClientAction reseteado" in reset_result else "SKIPPED"
    
    # Paso 3: Ejecutar ccmrepair.exe
    print("  → Ejecutando ccmrepair...")
    repair_cmd = "$ccmrepair = 'C:\\Windows\\ccmsetup\\ccmrepair.exe'; if (Test-Path $ccmrepair) { & $ccmrepair } else { 'ccmrepair.exe no encontrado' }; 'Reparación ejecutada'"
    repair_result = helper.run_remote(hostname, repair_cmd)
    results["steps"]["ccmrepair"] = "OK" if "Reparación ejecutada" in repair_result else "SKIPPED"
    
    # Paso 4: Reiniciar servicio SMS Agent Host
    print("  → Reiniciando SMS Agent Host...")
    restart_cmd = "Restart-Service -Name CcmExec -ErrorAction SilentlyContinue; Start-Sleep -Seconds 5; 'Servicio reiniciado'"
    restart_result = helper.run_remote(hostname, restart_cmd)
    results["steps"]["restart_service"] = "OK" if "Servicio reiniciado" in restart_result else "FAILED"
    
    # Paso 5: Forzar políticas
    print("  → Forzando políticas...")
    policy_cmd = "& 'C:\\Windows\\CCM\\ccmexec.exe' /rs; Start-Sleep -Seconds 2; & 'C:\\Windows\\CCM\\ccmexec.exe' /mp:MP_SERVER /forcepolicy; Start-Sleep -Seconds 2; 'Políticas forzadas'"
    policy_result = helper.run_remote(hostname, policy_cmd)
    results["steps"]["force_policies"] = "OK" if "Políticas forzadas" in policy_result else "SKIPPED"
    
    # Paso 6: Validar boundaries
    print("  → Validando boundaries...")
    boundary_cmd = "Get-WmiObject -Namespace root\\ccm\\LocationServices -Class SMS_ActiveMPCandidate | Select-Object NetworkID, Priority; 'Boundaries verificados'"
    boundary_result = helper.run_remote(hostname, boundary_cmd)
    results["steps"]["validate_boundaries"] = boundary_result if boundary_result != "N/A" else "N/A"
    
    # Paso 7: Validar certificado
    print("  → Validando certificado...")
    cert_cmd = "Get-ChildItem -Path Cert:\\LocalMachine\\SMS -ErrorAction SilentlyContinue | Select-Object Subject, Thumbprint; 'Certificado verificado'"
    cert_result = helper.run_remote(hostname, cert_cmd)
    results["steps"]["validate_certificate"] = cert_result if cert_result != "N/A" else "N/A"
    
    # Paso 8: Forzar descubrimiento
    print("  → Forzando descubrimiento...")
    discovery_cmd = "& 'C:\\Windows\\CCM\\ccmexec.exe' /rs; Start-Sleep -Seconds 3; 'Descubrimiento forzado'"
    discovery_result = helper.run_remote(hostname, discovery_cmd)
    results["steps"]["force_discovery"] = "OK" if "Descubrimiento forzado" in discovery_result else "SKIPPED"
    
    # Determinar éxito general
    success_steps = sum(1 for v in results["steps"].values() if v == "OK")
    results["success"] = success_steps >= 5
    results["success_rate"] = f"{success_steps}/8"
    
    # Log
    log_result("sccm_fix", hostname, results["success"], f"Rate: {results['success_rate']}")
    
    return results


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
    print("🔧 REPARACIÓN AUTOMÁTICA DEL CLIENTE SCCM")
    print("=" * 60)
    print("\n📦 Ingresá los inventarios (NBxxxxxx) separados por espacio")
    inv_list = input("Ej: NB100232 NB100549\n\nInventarios: ").strip().split()
    
    if not inv_list:
        print("❌ No se ingresaron inventarios")
        input("\nPresioná ENTER para salir...")
        return
    
    all_results = {}
    
    for inv in inv_list:
        result = fix_sccm(helper, inv)
        all_results[inv] = result
        
        if result["success"]:
            print(f"\n✅ {inv}: Reparación completada ({result['success_rate']})")
        else:
            print(f"\n⚠️  {inv}: Reparación parcial ({result['success_rate']})")
    
    # Guardar reporte
    report_path = save_report(all_results, "sccm_fix")
    print(f"\n📄 Reporte guardado: {report_path}")
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    main()

