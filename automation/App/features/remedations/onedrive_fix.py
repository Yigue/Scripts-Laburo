"""
Script de reparación automática de OneDrive
Resuelve problemas comunes de sincronización sin tocar físicamente el equipo
"""
import sys
import os
from datetime import datetime

# Agregar el directorio padre al path para importar utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.psexec_helper import PsExecHelper, log_result
from utils.common import save_report, clear_screen, load_config, get_credentials


def fix_onedrive(helper, hostname):
    """
    Ejecuta la reparación completa de OneDrive
    
    Args:
        helper: Instancia de PsExecHelper
        hostname: Hostname del equipo
    
    Returns:
        dict: Resultado de la reparación
    """
    print(f"\n🔧 Reparando OneDrive en {hostname}...")
    results = {
        "hostname": hostname,
        "timestamp": datetime.now().isoformat(),
        "steps": {}
    }
    
    # Paso 1: Detener procesos OneDrive
    print("  → Deteniendo procesos OneDrive...")
    stop_cmd = "Get-Process -Name OneDrive -ErrorAction SilentlyContinue | Stop-Process -Force"
    stop_result = helper.run_remote(hostname, stop_cmd, verbose=False)
    results["steps"]["stop_processes"] = "OK" if stop_result != "N/A" else "SKIPPED"
    
    # Paso 2: Reset completo de OneDrive
    print("  → Ejecutando reset completo...")
    reset_cmd = "$onedrive = (Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders').{374DE290-123F-4565-9164-39C4925E467B}; if (Test-Path \"$env:LOCALAPPDATA\\Microsoft\\OneDrive\\onedrive.exe\") { & \"$env:LOCALAPPDATA\\Microsoft\\OneDrive\\onedrive.exe\" /reset } else { 'OneDrive no encontrado' }"
    reset_result = helper.run_remote(hostname, reset_cmd)
    results["steps"]["reset"] = "OK" if "OneDrive no encontrado" not in reset_result else "FAILED"
    
    # Paso 3: Limpiar cache corrupta
    print("  → Limpiando cache...")
    cache_cmd = "Remove-Item -Path \"$env:LOCALAPPDATA\\Microsoft\\OneDrive\\logs\" -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path \"$env:LOCALAPPDATA\\Microsoft\\OneDrive\\settings\" -Recurse -Force -ErrorAction SilentlyContinue; 'Cache limpiado'"
    cache_result = helper.run_remote(hostname, cache_cmd)
    results["steps"]["clear_cache"] = "OK" if "Cache limpiado" in cache_result else "FAILED"
    
    # Paso 4: Reiniciar servicio
    print("  → Reiniciando servicio...")
    service_cmd = "Restart-Service -Name 'OneSyncSvc' -ErrorAction SilentlyContinue; 'Servicio reiniciado'"
    service_result = helper.run_remote(hostname, service_cmd)
    results["steps"]["restart_service"] = "OK" if "Servicio reiniciado" in service_result else "SKIPPED"
    
    # Paso 5: Verificar archivos en conflicto
    print("  → Verificando conflictos...")
    conflict_cmd = "Get-ChildItem -Path \"$env:USERPROFILE\\OneDrive\" -Recurse -Filter '*conflict*' -ErrorAction SilentlyContinue | Select-Object -First 5 | ForEach-Object { $_.FullName }"
    conflicts = helper.run_remote(hostname, conflict_cmd)
    results["steps"]["check_conflicts"] = conflicts if conflicts != "N/A" else "Sin conflictos detectados"
    
    # Paso 6: Iniciar OneDrive nuevamente
    print("  → Iniciando OneDrive...")
    start_cmd = "Start-Process -FilePath \"$env:LOCALAPPDATA\\Microsoft\\OneDrive\\onedrive.exe\" -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2; 'OneDrive iniciado'"
    start_result = helper.run_remote(hostname, start_cmd)
    results["steps"]["start_onedrive"] = "OK" if "OneDrive iniciado" in start_result else "FAILED"
    
    # Determinar éxito general
    success_steps = sum(1 for v in results["steps"].values() if v == "OK")
    results["success"] = success_steps >= 4
    results["success_rate"] = f"{success_steps}/6"
    
    # Log
    log_result("onedrive_fix", hostname, results["success"], f"Rate: {results['success_rate']}")
    
    return results


def main():
    """Función principal"""
    clear_screen()
    config = load_config()
    
    print("=" * 60)
    print("🔧 REPARACIÓN AUTOMÁTICA DE ONEDRIVE")
    print("=" * 60)
    print("\n📦 Ingresá los inventarios (NBxxxxxx) separados por espacio")
    inv_list = input("Ej: NB100232 NB100549\n\nInventarios: ").strip().split()
    
    if not inv_list:
        print("❌ No se ingresaron inventarios")
        input("\nPresioná ENTER para salir...")
        return
    
    # Solicitar credenciales
    user, password = get_credentials()
    
    helper = PsExecHelper(
        psexec_path=config.get("psexec_path", "PsExec.exe"),
        remote_user=user,
        remote_pass=password
    )
    
    all_results = {}
    
    for inv in inv_list:
        result = fix_onedrive(helper, inv)
        all_results[inv] = result
        
        if result["success"]:
            print(f"\n✅ {inv}: Reparación completada ({result['success_rate']})")
        else:
            print(f"\n⚠️  {inv}: Reparación parcial ({result['success_rate']})")
    
    # Guardar reporte
    report_path = save_report(all_results, "onedrive_fix")
    print(f"\n📄 Reporte guardado: {report_path}")
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    main()

