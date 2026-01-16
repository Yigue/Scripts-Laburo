# cli/widgets.py
from rich.console import Console
from rich.prompt import Prompt
import questionary
from functools import lru_cache

class QuickActions:
    def __init__(self):
        self.console = Console()
        self.favorites = self.load_favorites()
    
    @lru_cache(maxsize=128)
    def cached_host_info(self, hostname):
        """Cache de información de hosts para respuestas rápidas"""
        # Implementar cache para consultas frecuentes
        pass
    
    def quick_menu(self):
        """Menú rápido con atajos"""
        while True:
            action = questionary.select(
                "🛠️ Quick Actions:",
                choices=[
                    "🔓 Unlock User (AD)",
                    "🔑 Get LAPS Password",
                    "🔄 gpupdate /force",
                    "📶 WiFi Diagnostics",
                    "💾 Check Disk Space",
                    "🖨️ Printer Fix",
                    "🚀 SCCM Machine Policy",
                    "⚡ Speed Test",
                    "📊 System Specs",
                    "🔙 Volver al menú principal"
                ],
                qmark="⚡"
            ).ask()
            
            if "Volver" in action:
                break
            
            # Ejecutar acción rápida
            self.execute_quick_action(action)
    
    def execute_quick_action(self, action):
        """Ejecutar acción sin menús intermedios"""
        action_map = {
            "🔓 Unlock User": lambda: self.run_playbook("admin/unlock_user.yml"),
            "🔑 Get LAPS Password": lambda: self.run_playbook("admin/get_laps_password.yml"),
            # ... más mapeos
        }
        
        if action in action_map:
            with self.console.status("[bold green]Ejecutando...[/bold green]"):
                result = action_map[action]()
                self.console.print(f"[green]✓ {action} completado[/green]")