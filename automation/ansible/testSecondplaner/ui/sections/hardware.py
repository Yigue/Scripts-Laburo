"""
Sección Hardware/Diagnostics
"""
import questionary
from typing import TYPE_CHECKING

from config.menu_data import MENU_DATA
from ui.sections.base_section import BaseSection

if TYPE_CHECKING:
    from core.context import AppContext
    from core.engine import BackgroundEngine


class HardwareSection(BaseSection):
    """Sección Hardware y Diagnostics"""
    
    def run(self) -> None:
        """Ejecutar menú Hardware"""
        while True:
            self.console.clear()
            self._show_header()
            
            actions = MENU_DATA.get("💻 Hardware", [])
            choices = [f"{a['name']}" for a in actions]
            choices.append("⬅️ Volver")
            
            action_name = questionary.select(
                "🔧 Hardware / Diagnostics",
                choices=choices
            ).ask()
            
            if not action_name or action_name == "⬅️ Volver":
                break
            
            selected_action = next((a for a in actions if a["name"] == action_name), None)
            
            if selected_action:
                self.execute_action(selected_action)
                input("\nPresiona Enter para continuar...")
    
    def _show_header(self) -> None:
        """Mostrar header de la sección"""
        self.console.print("[bold cyan]🔧 Hardware / Diagnostics[/bold cyan]")
        self.console.print("[dim]Diagnósticos y gestión de hardware[/dim]\n")
