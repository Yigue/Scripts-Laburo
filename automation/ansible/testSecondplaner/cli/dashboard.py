# cli/dashboard.py
from rich.console import Console, Group
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.spinner import Spinner
import time
from datetime import datetime

class LiveDashboard:
    def __init__(self):
        self.console = Console()
        self.metrics = {}
        
    def get_system_metrics(self):
        """Obtener métricas del sistema (simulado)"""
        return {
            'active_tasks': 3,
            'hosts_online': 24,
            'hosts_offline': 2,
            'alerts': ['WLC01 - High latency', 'SRV02 - Disk > 85%'],
            'last_checked': datetime.now().strftime("%H:%M:%S"),
            'performance': {
                'cpu': 45,
                'memory': 78,
                'network': 120  # Mbps
            }
        }
    
    def create_metric_panel(self):
        """Crear panel de métricas visual"""
        metrics = self.get_system_metrics()
        
        # Tabla de métricas principales
        main_table = Table(title="📈 Métricas Principales")
        main_table.add_column("Métrica", style="cyan")
        main_table.add_column("Valor", style="white")
        main_table.add_column("Estado", style="green")
        
        main_table.add_row("Hosts Online", str(metrics['hosts_online']), "✅")
        main_table.add_row("Hosts Offline", str(metrics['hosts_offline']), "⚠️" if metrics['hosts_offline'] > 0 else "✅")
        main_table.add_row("Tareas Activas", str(metrics['active_tasks']), "🔄")
        main_table.add_row("Última Verificación", metrics['last_checked'], "📊")
        
        # Tabla de rendimiento
        perf_table = Table(title="⚡ Rendimiento")
        perf_table.add_column("Componente", style="cyan")
        perf_table.add_column("Uso", style="white")
        perf_table.add_column("Barra", style="green")
        
        for comp, value in metrics['performance'].items():
            bar = "█" * (value // 10) + "░" * (10 - (value // 10))
            color = "green" if value < 70 else "yellow" if value < 85 else "red"
            perf_table.add_row(comp.upper(), f"{value}%", f"[{color}]{bar}[/{color}]")
        
        # Alertas
        alert_panel = Panel(
            "\n".join([f"🔴 {alert}" for alert in metrics['alerts']]) or "✅ Sin alertas",
            title="🚨 Alertas Activas",
            border_style="red" if metrics['alerts'] else "green"
        )
        
        return Panel(
            Group(main_table, perf_table, alert_panel),
            title="📊 Dashboard en Tiempo Real"
        )
    
    def monitor(self):
        """Ejecutar dashboard auto-actualizable"""
        self.console.clear()
        
        with Live(self.create_metric_panel(), refresh_per_second=2, screen=True) as live:
            try:
                while True:
                    live.update(self.create_metric_panel())
                    time.sleep(5)  # Actualizar cada 5 segundos
            except KeyboardInterrupt:
                self.console.print("[yellow]Dashboard detenido[/yellow]")