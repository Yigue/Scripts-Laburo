"""
Sección WLC Cisco
"""
import questionary
from typing import TYPE_CHECKING

from config.menu_data import MENU_DATA
from ui.sections.base_section import BaseSection

if TYPE_CHECKING:
    from core.context import AppContext
    from core.engine import BackgroundEngine


class WLCSection(BaseSection):
    """Sección WLC Cisco"""
    
    def run(self) -> None:
        """Ejecutar menú WLC"""
        while True:
            self.console.clear()
            self._show_header()
            
            actions = MENU_DATA.get("🌐 WLC Cisco", [])
            choices = [f"{a['name']}" for a in actions]
            choices.append("⬅️ Volver")
            
            action_name = questionary.select(
                "🌐 WLC Cisco",
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
        self.console.print("[bold cyan]🌐 WLC Cisco[/bold cyan]")
        self.console.print("[dim]Gestión de Wireless Controller[/dim]\n")
        if self.context.wlc_profile:
            self.console.print(f"[green]Perfil activo: {self.context.wlc_profile}[/green]\n")
        else:
            self.console.print("[yellow]⚠ No hay perfil WLC configurado[/yellow]\n")
