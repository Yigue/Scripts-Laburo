"""
Script de reparación automática de VPN (FortiClient)
Resuelve problemas de conexión, cache SSL y configuración
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.psexec_helper import PsExecHelper, log_result
from utils.common import save_report, clear_screen, load_config


def fix_vpn(helper, hostname):
    """
    Ejecuta la reparación completa de VPN
    
    Args:
        helper: Instancia de PsExecHelper
        hostname: Hostname del equipo
    
    Returns:
        dict: Resultado de la reparación
    """
    print(f"\n🔧 Reparando VPN en {hostname}...")
    results = {
        "hostname": hostname,
        "timestamp": datetime.now().isoformat(),
        "steps": {}
    }
    
    # Paso 1: Cerrar FortiClient
    print("  → Cerrando FortiClient...")
    close_cmd = "Get-Process -Name FortiClient,FortiTray -ErrorAction SilentlyContinue | Stop-Process -Force; Start-Sleep -Seconds 2; 'FortiClient cerrado'"
    close_result = helper.run_remote(hostname, close_cmd)
    results["steps"]["close_forticlient"] = "OK" if "FortiClient cerrado" in close_result else "SKIPPED"
    
    # Paso 2: Borrar cache SSL
    print("  → Limpiando cache SSL...")
    ssl_cmd = "Remove-Item -Path \"$env:LOCALAPPDATA\\Fortinet\\FortiClient\\ssl\" -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path \"$env:APPDATA\\Fortinet\\FortiClient\\ssl\" -Recurse -Force -ErrorAction SilentlyContinue; 'Cache SSL limpiado'"
    ssl_result = helper.run_remote(hostname, ssl_cmd)
    results["steps"]["clear_ssl_cache"] = "OK" if "Cache SSL limpiado" in ssl_result else "SKIPPED"
    
    # Paso 3: Regenerar configuración
    print("  → Regenerando configuración...")
    config_cmd = "Remove-Item -Path \"$env:LOCALAPPDATA\\Fortinet\\FortiClient\\config\" -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path \"$env:APPDATA\\Fortinet\\FortiClient\\config\" -Recurse -Force -ErrorAction SilentlyContinue; 'Configuración regenerada'"
    config_result = helper.run_remote(hostname, config_cmd)
    results["steps"]["regenerate_config"] = "OK" if "Configuración regenerada" in config_result else "SKIPPED"
    
    # Paso 4: Reset de DNS
    print("  → Reseteando DNS...")
    dns_cmd = "ipconfig /flushdns; 'DNS reseteado'"
    dns_result = helper.run_remote(hostname, dns_cmd)
    results["steps"]["reset_dns"] = "OK" if "DNS reseteado" in dns_result else "FAILED"
    
    # Paso 5: Reiniciar adaptador VPN
    print("  → Reiniciando adaptador VPN...")
    adapter_cmd = "$adapter = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like '*Forti*' -or $_.Name -like '*Forti*' }; if ($adapter) { Disable-NetAdapter -Name $adapter.Name -Confirm:$false; Start-Sleep -Seconds 3; Enable-NetAdapter -Name $adapter.Name -Confirm:$false; 'Adaptador reiniciado' } else { 'Adaptador VPN no encontrado' }"
    adapter_result = helper.run_remote(hostname, adapter_cmd)
    results["steps"]["restart_adapter"] = "OK" if "Adaptador reiniciado" in adapter_result else "SKIPPED"
    
    # Paso 6: Limpiar certificados viejos
    print("  → Limpiando certificados...")
    cert_cmd = "Remove-Item -Path \"$env:LOCALAPPDATA\\Fortinet\\FortiClient\\cert\" -Recurse -Force -ErrorAction SilentlyContinue; 'Certificados limpiados'"
    cert_result = helper.run_remote(hostname, cert_cmd)
    results["steps"]["clear_certificates"] = "OK" if "Certificados limpiados" in cert_result else "SKIPPED"
    
    # Paso 7: Forzar reconexión (iniciar FortiClient)
    print("  → Iniciando FortiClient...")
    start_cmd = "$fortiPath = 'C:\\Program Files\\Fortinet\\FortiClient\\FortiClient.exe'; if (Test-Path $fortiPath) { Start-Process -FilePath $fortiPath; Start-Sleep -Seconds 3; 'FortiClient iniciado' } else { 'FortiClient no encontrado en ruta estándar' }"
    start_result = helper.run_remote(hostname, start_cmd)
    results["steps"]["start_forticlient"] = "OK" if "FortiClient iniciado" in start_result else "SKIPPED"
    
    # Determinar éxito general
    success_steps = sum(1 for v in results["steps"].values() if v == "OK")
    results["success"] = success_steps >= 4
    results["success_rate"] = f"{success_steps}/7"
    
    # Log
    log_result("vpn_fix", hostname, results["success"], f"Rate: {results['success_rate']}")
    
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
    print("🔧 REPARACIÓN AUTOMÁTICA DE VPN (FORTICLIENT)")
    print("=" * 60)
    print("\n📦 Ingresá los inventarios (NBxxxxxx) separados por espacio")
    inv_list = input("Ej: NB100232 NB100549\n\nInventarios: ").strip().split()
    
    if not inv_list:
        print("❌ No se ingresaron inventarios")
        input("\nPresioná ENTER para salir...")
        return
    
    all_results = {}
    
    for inv in inv_list:
        result = fix_vpn(helper, inv)
        all_results[inv] = result
        
        if result["success"]:
            print(f"\n✅ {inv}: Reparación completada ({result['success_rate']})")
        else:
            print(f"\n⚠️  {inv}: Reparación parcial ({result['success_rate']})")
    
    # Guardar reporte
    report_path = save_report(all_results, "vpn_fix")
    print(f"\n📄 Reporte guardado: {report_path}")
    input("\nPresioná ENTER para salir...")


if __name__ == "__main__":
    main()

