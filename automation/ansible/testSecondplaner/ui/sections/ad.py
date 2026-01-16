"""
Sección AD - Active Directory
"""
import questionary
from typing import TYPE_CHECKING

from config.menu_data import MENU_DATA
from ui.sections.base_section import BaseSection

if TYPE_CHECKING:
    from core.context import AppContext
    from core.engine import BackgroundEngine


class ADSection(BaseSection):
    """Sección Active Directory"""
    
    def run(self) -> None:
        """Ejecutar menú AD"""
        while True:
            self.console.clear()
            self._show_header()
            
            # Separar en consultas y acciones
            ad_actions = MENU_DATA.get("🔐 Active Directory", [])
            consultas = [a for a in ad_actions if a.get("action_type") == "read-only"]
            acciones = [a for a in ad_actions if a.get("action_type") != "read-only"]
            
            choices = []
            if consultas:
                choices.extend([f"📋 {a['name']}" for a in consultas])
            if acciones:
                choices.extend([f"⚙️ {a['name']}" for a in acciones])
            choices.append("⬅️ Volver")
            
            action_name = questionary.select(
                "🔐 Active Directory",
                choices=choices
            ).ask()
            
            if not action_name or action_name == "⬅️ Volver":
                break
            
            # Encontrar la acción seleccionada
            selected_action = None
            for action in ad_actions:
                if action["name"] in action_name:
                    selected_action = action
                    break
            
            if selected_action:
                self.execute_action(selected_action)
                input("\nPresiona Enter para continuar...")
    
    def _show_header(self) -> None:
        """Mostrar header de la sección"""
        self.console.print("[bold cyan]🔐 Active Directory[/bold cyan]")
        self.console.print("[dim]Consultas y gestión de usuarios[/dim]\n")
