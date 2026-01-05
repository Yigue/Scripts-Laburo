"""
DiagnosticSuite - Suite completa de diagnósticos automáticos
Ejecuta múltiples verificaciones y genera reporte
"""
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from domain.models import Host
from infrastructure.health import HealthChecker, DependencyValidator
from infrastructure.logging import get_logger
from shared.reporting import ReportGenerator, ReportEntry


@dataclass
class DiagnosticResult:
    """Resultado de un diagnóstico"""
    name: str
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0


class DiagnosticSuite:
    """Suite completa de diagnósticos automáticos"""
    
    def __init__(self, executor):
        """
        Inicializa la suite
        
        Args:
            executor: Ejecutor remoto
        """
        self.executor = executor
        self.health_checker = HealthChecker(executor)
        self.logger = get_logger()
        self.results: List[DiagnosticResult] = []
    
    def run_all_diagnostics(self, host: Host) -> Dict[str, Any]:
        """
        Ejecuta todos los diagnósticos
        
        Args:
            host: Host a diagnosticar
            
        Returns:
            Dict con resultados completos
        """
        print(f"\n🔍 EJECUTANDO DIAGNÓSTICOS COMPLETOS EN {host.hostname}")
        print("=" * 70)
        print()
        
        start_time = datetime.now()
        self.results = []
        
        # 1. Conectividad
        print("1️⃣ Verificando conectividad...")
        self._check_connectivity(host)
        
        # 2. Espacio en disco
        print("2️⃣ Verificando espacio en disco...")
        self._check_disk_space(host)
        
        # 3. Servicios críticos
        print("3️⃣ Verificando servicios críticos...")
        self._check_critical_services(host)
        
        # 4. Salud de red
        print("4️⃣ Verificando red...")
        self._check_network(host)
        
        # 5. Actualizaciones
        print("5️⃣ Verificando actualizaciones...")
        self._check_updates(host)
        
        # Calcular duración total
        duration = (datetime.now() - start_time).total_seconds()
        
        # Generar resumen
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        print()
        print("=" * 70)
        print(f"✅ DIAGNÓSTICOS COMPLETADOS")
        print(f"   Total: {total} | Pasados: {passed} | Fallidos: {total - passed}")
        print(f"   Duración: {duration:.2f}s")
        print("=" * 70)
        
        return {
            "hostname": host.hostname,
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "total_checks": total,
            "passed": passed,
            "failed": total - passed,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details
                }
                for r in self.results
            ]
        }
    
    def _check_connectivity(self, host: Host):
        """Verifica conectividad básica"""
        try:
            connectivity = self.health_checker.check_connectivity(host)
            
            passed = connectivity["healthy"]
            details = {
                "ping": connectivity["ping"],
                "winrm": connectivity["winrm"],
                "smb": connectivity["smb"]
            }
            
            if passed:
                message = "✅ Conectividad OK"
            else:
                message = "❌ Problemas de conectividad"
            
            self.results.append(DiagnosticResult(
                name="Conectividad",
                passed=passed,
                message=message,
                details=details
            ))
            
            print(f"   {message}")
            
        except Exception as e:
            self.results.append(DiagnosticResult(
                name="Conectividad",
                passed=False,
                message=f"Error: {e}"
            ))
            print(f"   ❌ Error: {e}")
    
    def _check_disk_space(self, host: Host):
        """Verifica espacio en disco"""
        try:
            disk = self.health_checker.check_disk_space(host, required_gb=10.0)
            
            passed = disk["sufficient"]
            free_gb = disk["free_gb"]
            
            if passed:
                message = f"✅ Espacio suficiente: {free_gb:.1f} GB libres"
            else:
                message = f"⚠️ Poco espacio: {free_gb:.1f} GB libres"
            
            self.results.append(DiagnosticResult(
                name="Espacio en disco",
                passed=passed,
                message=message,
                details={"free_gb": free_gb}
            ))
            
            print(f"   {message}")
            
        except Exception as e:
            self.results.append(DiagnosticResult(
                name="Espacio en disco",
                passed=False,
                message=f"Error: {e}"
            ))
            print(f"   ❌ Error: {e}")
    
    def _check_critical_services(self, host: Host):
        """Verifica servicios críticos"""
        try:
            script = """
$critical = @('wuauserv', 'Winmgmt', 'W32Time', 'EventLog')
$problems = @()
foreach ($svc in $critical) {
    $service = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if (!$service -or $service.Status -ne 'Running') {
        $problems += $svc
    }
}
if ($problems.Count -gt 0) {
    Write-Output "PROBLEMS:$($problems -join ',')"
} else {
    Write-Output "OK"
}
"""
            output = self.executor.run_script_block(host.hostname, script, timeout=30, verbose=False)
            
            if output and "OK" in output:
                passed = True
                message = "✅ Servicios críticos OK"
            else:
                passed = False
                message = "⚠️ Algunos servicios tienen problemas"
            
            self.results.append(DiagnosticResult(
                name="Servicios críticos",
                passed=passed,
                message=message
            ))
            
            print(f"   {message}")
            
        except Exception as e:
            self.results.append(DiagnosticResult(
                name="Servicios críticos",
                passed=False,
                message=f"Error: {e}"
            ))
            print(f"   ❌ Error: {e}")
    
    def _check_network(self, host: Host):
        """Verifica configuración de red"""
        try:
            script = """
$adapter = Get-NetAdapter | Where-Object Status -eq 'Up' | Select-Object -First 1
if ($adapter) { Write-Output "OK" } else { Write-Output "FAIL" }
"""
            output = self.executor.run_script_block(host.hostname, script, timeout=30, verbose=False)
            
            passed = output and "OK" in output
            message = "✅ Adaptadores de red OK" if passed else "❌ Sin adaptadores activos"
            
            self.results.append(DiagnosticResult(
                name="Red",
                passed=passed,
                message=message
            ))
            
            print(f"   {message}")
            
        except Exception as e:
            self.results.append(DiagnosticResult(
                name="Red",
                passed=False,
                message=f"Error: {e}"
            ))
            print(f"   ❌ Error: {e}")
    
    def _check_updates(self, host: Host):
        """Verifica actualizaciones pendientes"""
        try:
            script = """
try {
    $updates = (New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher().Search("IsInstalled=0")
    Write-Output "COUNT:$($updates.Updates.Count)"
} catch {
    Write-Output "ERROR"
}
"""
            output = self.executor.run_script_block(host.hostname, script, timeout=60, verbose=False)
            
            if output and "COUNT:" in output:
                count = int(output.split("COUNT:")[1].strip())
                passed = count < 10
                message = f"{'✅' if passed else '⚠️'} {count} actualizaciones pendientes"
            else:
                passed = True
                message = "ℹ️ No se pudo verificar actualizaciones"
            
            self.results.append(DiagnosticResult(
                name="Actualizaciones",
                passed=passed,
                message=message
            ))
            
            print(f"   {message}")
            
        except Exception as e:
            self.results.append(DiagnosticResult(
                name="Actualizaciones",
                passed=True,  # No crítico
                message=f"No verificado: {e}"
            ))
            print(f"   ℹ️ No verificado: {e}")


def run_full_diagnostics(executor, hostname: str):
    """
    Función helper para ejecutar diagnósticos completos
    
    Args:
        executor: Ejecutor remoto
        hostname: Nombre del host
    """
    host = Host(hostname=hostname)
    suite = DiagnosticSuite(executor)
    results = suite.run_all_diagnostics(host)
    
    # Ofrecer guardar reporte
    save = input("\n¿Guardar reporte? (S/N): ").strip().upper()
    if save == "S":
        generator = ReportGenerator()
        entries = [
            ReportEntry(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                hostname=hostname,
                operation=r["name"],
                status="SUCCESS" if r["passed"] else "FAILED",
                duration=0.0,
                details=r["message"]
            )
            for r in results["results"]
        ]
        
        filepath = generator.generate_operations_report(entries, format="txt")
        print(f"\n📄 Reporte guardado: {filepath}")
    
    input("\nPresioná ENTER para continuar...")

