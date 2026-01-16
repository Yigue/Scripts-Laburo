"""
Sección WiFi/Network
"""
import questionary
from typing import TYPE_CHECKING

from config.menu_data import MENU_DATA
from ui.sections.base_section import BaseSection

if TYPE_CHECKING:
    from core.context import AppContext
    from core.engine import BackgroundEngine


class NetworkSection(BaseSection):
    """Sección WiFi y Network"""
    
    def run(self) -> None:
        """Ejecutar menú Network"""
        while True:
            self.console.clear()
            self._show_header()
            
            actions = MENU_DATA.get("📶 Red y WIFI", [])
            
            # Separar local vs remoto
            local_actions = [a for a in actions if not a.get("requires_target")]
            remote_actions = [a for a in actions if a.get("requires_target")]
            
            choices = []
            if local_actions:
                choices.extend([f"🖥️ {a['name']}" for a in local_actions])
            if remote_actions:
                choices.extend([f"🌐 {a['name']}" for a in remote_actions])
            choices.append("⬅️ Volver")
            
            action_name = questionary.select(
                "📶 WiFi / Network",
                choices=choices
            ).ask()
            
            if not action_name or action_name == "⬅️ Volver":
                break
            
            # Encontrar la acción (remover emoji)
            clean_name = action_name.replace("🖥️ ", "").replace("🌐 ", "")
            selected_action = next((a for a in actions if a["name"] == clean_name), None)
            
            if selected_action:
                self.execute_action(selected_action)
                input("\nPresiona Enter para continuar...")
    
    def _show_header(self) -> None:
        """Mostrar header de la sección"""
        self.console.print("[bold cyan]📶 WiFi / Network[/bold cyan]")
        self.console.print("[dim]Diagnósticos y reparación de red[/dim]\n")
