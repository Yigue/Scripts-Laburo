"""
Sección Settings - Configuración
"""
import questionary
from typing import TYPE_CHECKING
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

if TYPE_CHECKING:
    from core.context import AppContext
    from core.engine import BackgroundEngine


class SettingsSection:
    """Sección Settings"""
    
    def __init__(self, context: "AppContext", engine: "BackgroundEngine"):
        self.context = context
        self.engine = engine
        self.console = Console()
    
    def run(self) -> None:
        """Ejecutar menú Settings"""
        while True:
            self.console.clear()
            self._show_current_settings()
            
            action = questionary.select(
                "⚙️ Settings",
                choices=[
                    "Toggle Read-only Mode",
                    "Toggle Check Mode",
                    "Configurar Verbosity",
                    "Gestionar Perfil WLC",
                    "Gestionar Perfil de Credenciales",
                    "Resetear Contexto",
                    "⬅️ Volver"
                ]
            ).ask()
            
            if not action or action == "⬅️ Volver":
                break
            
            if action == "Toggle Read-only Mode":
                self._toggle_read_only()
            elif action == "Toggle Check Mode":
                self._toggle_check_mode()
            elif action == "Configurar Verbosity":
                self._set_verbosity()
            elif action == "Gestionar Perfil WLC":
                self._manage_wlc_profile()
            elif action == "Gestionar Perfil de Credenciales":
                self._manage_credentials_profile()
            elif action == "Resetear Contexto":
                self._reset_context()
            
            input("\nPresiona Enter para continuar...")
    
    def _show_current_settings(self) -> None:
        """Mostrar configuración actual"""
        settings_table = Table(title="Configuración Actual", show_header=False)
        settings_table.add_column("Propiedad", style="cyan")
        settings_table.add_column("Valor", style="white")
        
        ctx_dict = self.context.to_dict()
        settings_table.add_row("Read-only Mode", ctx_dict["read_only_mode"])
        settings_table.add_row("Check Mode", ctx_dict["check_mode"])
        settings_table.add_row("Verbosity", str(ctx_dict["verbosity"]))
        settings_table.add_row("WLC Profile", ctx_dict["wlc_profile"])
        settings_table.add_row("Credentials Profile", ctx_dict["credentials_profile"])
        
        self.console.print(Panel(settings_table, border_style="blue"))
    
    def _toggle_read_only(self) -> None:
        """Toggle read-only mode"""
        new_value = not self.context.read_only_mode
        self.context.read_only_mode = new_value
        self.context.save(persist=True)
        
        status = "activado" if new_value else "desactivado"
        self.console.print(f"[green]✓ Read-only mode {status}[/green]")
    
    def _toggle_check_mode(self) -> None:
        """Toggle check mode"""
        new_value = not self.context.check_mode
        self.context.check_mode = new_value
        self.context.save(persist=True)
        
        status = "activado" if new_value else "desactivado"
        self.console.print(f"[green]✓ Check mode {status}[/green]")
    
    def _set_verbosity(self) -> None:
        """Configurar nivel de verbosity"""
        choices = ["0 (Silent)", "1 (Minimal)", "2 (Normal)", "3 (Verbose)", "4 (Debug)"]
        selected = questionary.select("Nivel de verbosity:", choices=choices).ask()
        
        if selected:
            level = int(selected.split()[0])
            self.context.verbosity = level
            self.context.save(persist=True)
            self.console.print(f"[green]✓ Verbosity establecido en nivel {level}[/green]")
    
    def _manage_wlc_profile(self) -> None:
        """Gestionar perfil WLC"""
        if self.context.wlc_profile:
            action = questionary.select(
                f"Perfil actual: {self.context.wlc_profile}",
                choices=["Cambiar perfil", "Limpiar perfil", "⬅️ Volver"]
            ).ask()
            
            if action == "Cambiar perfil":
                new_profile = questionary.text("Nuevo perfil WLC:").ask()
                if new_profile:
                    self.context.wlc_profile = new_profile
                    self.context.save(persist=True)
                    self.console.print(f"[green]✓ Perfil WLC actualizado: {new_profile}[/green]")
            elif action == "Limpiar perfil":
                self.context.wlc_profile = None
                self.context.save(persist=True)
                self.console.print("[green]✓ Perfil WLC limpiado[/green]")
        else:
            new_profile = questionary.text("Ingresa el nombre del perfil WLC:").ask()
            if new_profile:
                self.context.wlc_profile = new_profile
                self.context.save(persist=True)
                self.console.print(f"[green]✓ Perfil WLC establecido: {new_profile}[/green]")
    
    def _manage_credentials_profile(self) -> None:
        """Gestionar perfil de credenciales"""
        # Por ahora solo mostrar/seleccionar, sin guardar passwords
        profiles = ["Default", "Domain Admin", "Local Admin", "Service Account"]
        
        selected = questionary.select(
            "Selecciona perfil de credenciales:",
            choices=profiles
        ).ask()
        
        if selected:
            self.context.credentials_profile = selected
            self.context.save(persist=True)
            self.console.print(f"[green]✓ Perfil de credenciales: {selected}[/green]")
            self.console.print("[dim]Nota: Las credenciales no se guardan en claro[/dim]")
    
    def _reset_context(self) -> None:
        """Resetear contexto completo"""
        if questionary.confirm(
            "¿Estás seguro de resetear todo el contexto? Esto limpiará targets y estado de sesión.",
            default=False
        ).ask():
            self.context.reset()
            self.console.print("[green]✓ Contexto reseteado[/green]")
