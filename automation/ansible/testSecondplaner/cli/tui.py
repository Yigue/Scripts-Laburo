# cli/tui.py
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn
import questionary
from time import sleep
import threading

class InteractiveTUI:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.running = True
        self.status_data = {
            'online_hosts': 0,
            'last_task': None,
            'pending_tasks': [],
            'alerts': []
        }
    
    def create_layout(self):
        # Divide la pantalla en secciones
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=2),
            Layout(name="status", size=5),
            Layout(name="footer", size=3)
        )
        
        # Panel superior con logo y estado
        header = Panel(
            "[bold cyan]IT-OPS AUTOMATION HUB[/bold cyan] | "
            "[green]●[/green] Online | "
            f"[yellow]Tasks: {len(self.status_data['pending_tasks'])}[/yellow]",
            title="Estación de Control"
        )
        
        # Panel principal con menú
        main_menu = self.create_main_menu()
        
        # Panel de estado en tiempo real
        status_panel = self.create_status_panel()
        
        # Panel inferior con atajos
        footer = Panel(
            "[F1] Ayuda | [F2] Historial | [F3] Favoritos | "
            "[F5] Refresh | [Ctrl+C] Salir",
            style="dim"
        )
        
        self.layout["header"].update(header)
        self.layout["main"].update(main_menu)
        self.layout["status"].update(status_panel)
        self.layout["footer"].update(footer)
    
    def create_main_menu(self):
        """Menú principal tipo dashboard"""
        table = Table(title="🏠 [bold]Menú Principal[/bold]", show_header=False)
        table.add_column("Opción", style="cyan", no_wrap=True)
        table.add_column("Descripción", style="white")
        table.add_column("Status", style="green")
        
        menu_items = [
            ("1️⃣", "AD & Seguridad", "✅ 12 hosts"),
            ("2️⃣", "SCCM Management", "⚠️ 3 pendientes"),
            ("3️⃣", "WiFi & Red", "✅ Online"),
            ("4️⃣", "Windows & Apps", "🔄 Monitoreando"),
            ("5️⃣", "Hardware", "✅ 45/50 OK"),
            ("6️⃣", "WLC Controller", "🌐 Conectado"),
            ("7️⃣", "Monitor Dashboard", "📊 Live"),
            ("8️⃣", "Quick Actions", "⚡ Rápidas"),
            ("9️⃣", "Historial", "📁 Ver logs"),
            ("0️⃣", "Configuración", "⚙️")
        ]
        
        for num, desc, status in menu_items:
            table.add_row(num, desc, status)
        
        return Panel(table, border_style="blue")
    
    def create_status_panel(self):
        """Panel de estado en tiempo real"""
        status_table = Table(show_header=False, box=None)
        status_table.add_column("Metrica", style="cyan")
        status_table.add_column("Valor", style="white")
        
        status_table.add_row("Hosts Online", f"[green]{self.status_data['online_hosts']}[/green]")
        status_table.add_row("Última Tarea", self.status_data['last_task'] or "Ninguna")
        status_table.add_row("Alertas Activas", f"[red]{len(self.status_data['alerts'])}[/red]" if self.status_data['alerts'] else "[green]0[/green]")
        status_table.add_row("CPU Usage", "[yellow]45%[/yellow]")
        status_table.add_row("Memoria Libre", "8.2 GB")
        
        return Panel(status_table, title="📊 Estado del Sistema")
    
    def update_status_thread(self):
        """Hilo que actualiza métricas en background"""
        while self.running:
            # Actualizar hosts online
            self.status_data['online_hosts'] = self.check_online_hosts()
            
            # Verificar alertas
            self.check_alerts()
            
            sleep(10)  # Actualizar cada 10 segundos
    
    def run(self):
        """Ejecuta la TUI principal"""
        # Iniciar hilo de monitoreo
        monitor_thread = threading.Thread(target=self.update_status_thread, daemon=True)
        monitor_thread.start()
        
        # Configurar atajos de teclado
        self.console.clear()
        
        with Live(self.layout, refresh_per_second=4, screen=True) as live:
            while self.running:
                try:
                    self.create_layout()  # Refrescar layout
                    
                    # Capturar entrada del usuario
                    choice = questionary.select(
                        "Seleccione una opción:",
                        choices=[
                            "1. AD & Seguridad",
                            "2. SCCM Management", 
                            "3. WiFi & Red",
                            "4. Windows & Apps",
                            "5. Hardware",
                            "6. WLC Controller",
                            "7. Dashboard Live",
                            "8. Quick Actions",
                            "9. Historial",
                            "0. Configuración",
                            "Q. Salir"
                        ]
                    ).ask()
                    
                    if choice == "Q. Salir":
                        self.running = False
                        break
                    
                    # Procesar selección
                    self.handle_selection(choice[0])
                    
                except KeyboardInterrupt:
                    self.running = False
                    break
        
        self.console.print("[yellow]Saliendo de IT-Ops Hub...[/yellow]")