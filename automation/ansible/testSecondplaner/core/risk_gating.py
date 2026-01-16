"""
Sistema de gating por riesgo para diferenciar acciones de consulta vs destructivas
"""
from typing import Optional, Dict, Any, TYPE_CHECKING
import questionary

if TYPE_CHECKING:
    from core.context import AppContext


ACTION_TYPES = {
    "read-only": "read-only",
    "modify": "modify",
    "destructive": "destructive"
}


def requires_confirmation(playbook_path: str, action_metadata: Dict[str, Any]) -> bool:
    """
    Determinar si una acción requiere confirmación
    
    Args:
        playbook_path: Ruta al playbook
        action_metadata: Metadatos de la acción desde menu_data
        
    Returns:
        True si requiere confirmación, False si es read-only
    """
    action_type = action_metadata.get("action_type", "read-only")
    return action_type in ("modify", "destructive")


def validate_read_only(action_metadata: Dict[str, Any], context: "AppContext") -> tuple[bool, Optional[str]]:
    """
    Validar si una acción puede ejecutarse en modo read-only
    
    Args:
        action_metadata: Metadatos de la acción
        context: Contexto de aplicación
        
    Returns:
        Tupla (is_allowed, error_message)
        - is_allowed: True si está permitido, False si está bloqueado
        - error_message: Mensaje de error si está bloqueado
    """
    if not context.read_only_mode:
        return True, None
    
    action_type = action_metadata.get("action_type", "read-only")
    
    if action_type == "read-only":
        return True, None
    
    action_name = action_metadata.get("name", "Esta acción")
    return False, f"[red]Read-only mode ON: {action_name} está bloqueada[/red]"


def confirm_action(
    action_name: str,
    impact_description: str,
    action_type: str = "modify",
    context: Optional["AppContext"] = None
) -> bool:
    """
    Mostrar impacto de una acción y pedir confirmación
    
    Args:
        action_name: Nombre de la acción
        impact_description: Descripción del impacto
        action_type: Tipo de acción (modify o destructive)
        context: Contexto de aplicación (para mostrar check mode)
        
    Returns:
        True si el usuario confirma, False si cancela
    """
    from rich.console import Console
    console = Console()
    
    # Mostrar información de la acción
    console.print(f"\n[yellow]⚠ Acción: {action_name}[/yellow]")
    console.print(f"[dim]Impacto: {impact_description}[/dim]")
    
    if context and context.check_mode:
        console.print("[cyan]ℹ Check mode: Se ejecutará en modo simulación[/cyan]")
    
    # Confirmación diferente según el tipo
    if action_type == "destructive":
        # Confirmación doble para acciones destructivas
        console.print("\n[red]⚠️ ACCIÓN DESTRUCTIVA[/red]")
        confirmation_text = questionary.text(
            f"Escribí '{action_name.upper()}' para confirmar:",
            validate=lambda text: text.upper() == action_name.upper()
        ).ask()
        return confirmation_text is not None
    else:
        # Confirmación simple para acciones modificadoras
        return questionary.confirm(
            f"¿Deseas continuar con {action_name}?",
            default=False
        ).ask() or False


def get_risk_level(playbook_path: str, action_metadata: Dict[str, Any]) -> str:
    """
    Obtener nivel de riesgo de una acción
    
    Args:
        playbook_path: Ruta al playbook
        action_metadata: Metadatos de la acción
        
    Returns:
        Nivel de riesgo: "low", "medium", "high"
    """
    action_type = action_metadata.get("action_type", "read-only")
    
    if action_type == "read-only":
        return "low"
    elif action_type == "modify":
        return "medium"
    elif action_type == "destructive":
        return "high"
    
    return "low"
