"""
Quick Commands - Biblioteca de comandos rápidos útiles
Comandos frecuentes pre-configurados listos para usar
"""
from typing import Dict, Callable
from domain.models import Host, OperationResult


class QuickCommands:
    """Biblioteca de comandos rápidos pre-configurados"""
    
    def __init__(self, executor):
        """
        Inicializa la biblioteca
        
        Args:
            executor: Ejecutor remoto
        """
        self.executor = executor
    
    def restart_explorer(self, host: Host) -> OperationResult:
        """Reinicia Explorer.exe"""
        script = """
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-Process explorer
Write-Output "✅ Explorer reiniciado"
"""
        return self._execute_quick(host, script, "Reiniciar Explorer")
    
    def flush_dns(self, host: Host) -> OperationResult:
        """Limpia caché DNS"""
        script = "ipconfig /flushdns"
        return self._execute_quick(host, script, "Flush DNS")
    
    def renew_ip(self, host: Host) -> OperationResult:
        """Renueva dirección IP"""
        script = """
ipconfig /release
Start-Sleep -Seconds 2
ipconfig /renew
Write-Output "✅ IP renovada"
"""
        return self._execute_quick(host, script, "Renew IP")
    
    def reset_winsock(self, host: Host) -> OperationResult:
        """Reset de Winsock"""
        script = """
netsh winsock reset
netsh int ip reset
Write-Output "✅ Winsock reseteado"
Write-Output "⚠️ Se requiere reinicio"
"""
        return self._execute_quick(host, script, "Reset Winsock")
    
    def clear_temp(self, host: Host) -> OperationResult:
        """Limpia archivos temporales"""
        script = """
$temp = "$env:TEMP\\*"
Remove-Item $temp -Recurse -Force -ErrorAction SilentlyContinue
Write-Output "✅ Temporales limpiados"
"""
        return self._execute_quick(host, script, "Limpiar Temporales")
    
    def empty_recycle_bin(self, host: Host) -> OperationResult:
        """Vacía papelera de reciclaje"""
        script = """
Clear-RecycleBin -Force -ErrorAction SilentlyContinue
Write-Output "✅ Papelera vaciada"
"""
        return self._execute_quick(host, script, "Vaciar Papelera")
    
    def check_disk_health(self, host: Host) -> OperationResult:
        """Verifica salud de disco"""
        script = """
$disks = Get-PhysicalDisk
foreach ($disk in $disks) {
    Write-Output "$($disk.FriendlyName): $($disk.HealthStatus)"
}
"""
        return self._execute_quick(host, script, "Check Disk Health")
    
    def list_startup_programs(self, host: Host) -> OperationResult:
        """Lista programas de inicio"""
        script = """
Get-CimInstance Win32_StartupCommand | 
    Select-Object Name, Command, Location | 
    Format-Table -AutoSize
"""
        return self._execute_quick(host, script, "Startup Programs")
    
    def get_system_uptime(self, host: Host) -> OperationResult:
        """Obtiene uptime del sistema"""
        script = """
$os = Get-CimInstance Win32_OperatingSystem
$uptime = (Get-Date) - $os.LastBootUpTime
Write-Output "Sistema iniciado: $($os.LastBootUpTime)"
Write-Output "Uptime: $($uptime.Days) días, $($uptime.Hours) horas"
"""
        return self._execute_quick(host, script, "System Uptime")
    
    def check_windows_updates(self, host: Host) -> OperationResult:
        """Verifica actualizaciones pendientes"""
        script = """
$updates = (New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher().Search("IsInstalled=0")
Write-Output "Actualizaciones pendientes: $($updates.Updates.Count)"
"""
        return self._execute_quick(host, script, "Check Updates")
    
    def _execute_quick(self, host: Host, script: str, operation_name: str) -> OperationResult:
        """Ejecuta un comando rápido"""
        result = OperationResult(success=False, message=f"Ejecutando: {operation_name}")
        
        try:
            # Agregar redirección Write-Host
            full_script = """
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
""" + script
            
            output = self.executor.run_script_block(host.hostname, full_script, timeout=60, verbose=False)
            
            if output:
                print(output)
                result.success = True
                result.data = output
                result.message = f"{operation_name} completado"
        except Exception as e:
            result.add_error(str(e))
        
        return result
    
    def get_commands_menu(self) -> Dict[str, tuple]:
        """
        Retorna diccionario de comandos para crear menú
        
        Returns:
            Dict: {key: (label, function)}
        """
        return {
            "1": ("Reiniciar Explorer", self.restart_explorer),
            "2": ("Flush DNS", self.flush_dns),
            "3": ("Renovar IP", self.renew_ip),
            "4": ("Reset Winsock", self.reset_winsock),
            "5": ("Limpiar temporales", self.clear_temp),
            "6": ("Vaciar papelera", self.empty_recycle_bin),
            "7": ("Check salud de disco", self.check_disk_health),
            "8": ("Programas de inicio", self.list_startup_programs),
            "9": ("System uptime", self.get_system_uptime),
            "10": ("Check actualizaciones", self.check_windows_updates),
        }


def ejecutar_quick_commands(executor, hostname: str):
    """
    Muestra menú de comandos rápidos
    
    Args:
        executor: Ejecutor remoto
        hostname: Nombre del host
    """
    host = Host(hostname=hostname)
    quick = QuickCommands(executor)
    commands = quick.get_commands_menu()
    
    while True:
        print(f"\n{'=' * 60}")
        print(f"⚡ COMANDOS RÁPIDOS - {hostname}")
        print("=" * 60)
        print()
        
        for key, (label, _) in sorted(commands.items(), key=lambda x: int(x[0])):
            print(f"   {key}. {label}")
        
        print()
        print("0. Volver")
        print("=" * 60)
        
        opcion = input("\nSeleccioná una opción: ").strip()
        
        if opcion == "0":
            break
        elif opcion in commands:
            _, func = commands[opcion]
            func(host)
            input("\nPresioná ENTER para continuar...")
        else:
            print("\n❌ Opción inválida")
            input("\nPresioná ENTER para continuar...")

