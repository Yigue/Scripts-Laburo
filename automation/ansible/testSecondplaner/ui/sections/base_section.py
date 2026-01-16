"""
Clase base para secciones del menú
"""
from typing import TYPE_CHECKING, Optional, Dict, Any
from rich.console import Console

if TYPE_CHECKING:
    from core.context import AppContext
    from core.engine import BackgroundEngine


class BaseSection:
    """Clase base para todas las secciones del menú"""
    
    def __init__(self, context: "AppContext", engine: "BackgroundEngine"):
        self.context = context
        self.engine = engine
        self.console = Console()
    
    def execute_action(
        self,
        action_metadata: Dict[str, Any],
        extra_vars: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Ejecutar una acción validando requisitos y confirmaciones
        
        Args:
            action_metadata: Metadatos de la acción desde menu_data
            extra_vars: Variables adicionales para el playbook
            
        Returns:
            Job ID si se lanzó correctamente, None si se canceló
        """
        from core.risk_gating import validate_read_only, requires_confirmation, confirm_action
        from core.validators import ensure_target, ensure_user, ensure_wlc_profile, validate_playbook_path
        from pathlib import Path
        
        playbook_path = action_metadata.get("playbook")
        action_name = action_metadata.get("name")
        
        # Validar que el playbook existe
        base_dir = Path(__file__).parent.parent.parent.parent
        is_valid, error_msg = validate_playbook_path(playbook_path, base_dir)
        if not is_valid:
            self.console.print(f"[red]Error: {error_msg}[/red]")
            return None
        
        # Validar read-only mode
        is_allowed, error_msg = validate_read_only(action_metadata, self.context)
        if not is_allowed:
            self.console.print(error_msg)
            return None
        
        # Asegurar requisitos
        if action_metadata.get("requires_target"):
            target = ensure_target(self.context, self.console)
            if not target:
                self.console.print("[yellow]Target requerido pero no proporcionado[/yellow]")
                return None
        else:
            target = self.context.target or "localhost"
        
        if action_metadata.get("requires_user"):
            user = ensure_user(self.context, self.console)
            if not user:
                self.console.print("[yellow]Username requerido pero no proporcionado[/yellow]")
                return None
            if extra_vars is None:
                extra_vars = {}
            extra_vars["username"] = user
        
        if action_metadata.get("requires_wlc_profile"):
            profile = ensure_wlc_profile(self.context, self.console)
            if not profile:
                self.console.print("[yellow]Perfil WLC requerido pero no proporcionado[/yellow]")
                return None
            if extra_vars is None:
                extra_vars = {}
            extra_vars["wlc_profile"] = profile
        
        # Confirmación si es necesaria
        if requires_confirmation(playbook_path, action_metadata):
            impact = action_metadata.get("impact_description", "Ejecutará la acción")
            action_type = action_metadata.get("action_type", "modify")
            
            if not confirm_action(action_name, impact, action_type, self.context):
                self.console.print("[yellow]Acción cancelada[/yellow]")
                return None
        
        # Agregar check_mode y verbosity si están activos
        if extra_vars is None:
            extra_vars = {}
        
        if self.context.check_mode:
            extra_vars["check_mode"] = True
        
        if self.context.verbosity > 0:
            extra_vars["verbosity"] = self.context.verbosity
        
        # Ejecutar playbook
        try:
            job_id = self.engine.launch_playbook(playbook_path, target, extra_vars)
            self.console.print(f"[green]✓ Tarea lanzada con ID: {job_id}[/green]")
            self.context.last_result = "OK"
            self.context.save()
            return job_id
        except Exception as e:
            self.console.print(f"[red]Error al lanzar tarea: {e}[/red]")
            self.context.last_result = "FAIL"
            self.context.save()
            return None
