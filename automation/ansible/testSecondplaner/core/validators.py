"""
Helpers de validación para asegurar requisitos antes de ejecutar acciones
"""
from pathlib import Path
from typing import Optional, TYPE_CHECKING
import questionary

if TYPE_CHECKING:
    from core.context import AppContext
    from rich.console import Console


def ensure_target(
    context: "AppContext",
    console: Optional["Console"] = None,
    prompt_message: Optional[str] = None
) -> Optional[str]:
    """
    Asegurar que hay un target activo. Si falta, lo pide al usuario.
    
    Args:
        context: Contexto de aplicación
        console: Console de Rich (opcional)
        prompt_message: Mensaje personalizado para el prompt
        
    Returns:
        Target activo o None si el usuario cancela
    """
    if context.target:
        return context.target
    
    # Pedir target al usuario
    message = prompt_message or "Ingresa el hostname/IP del target:"
    target = questionary.text(message).ask()
    
    if target:
        target = target.upper().strip()
        context.set_target(target)
        if console:
            console.print(f"[green]✓ Target establecido: {target}[/green]")
        return target
    
    return None


def ensure_user(
    context: "AppContext",
    console: Optional["Console"] = None,
    prompt_message: Optional[str] = None
) -> Optional[str]:
    """
    Asegurar que hay un username. Lo pide al usuario.
    
    Args:
        context: Contexto de aplicación
        console: Console de Rich (opcional)
        prompt_message: Mensaje personalizado para el prompt
        
    Returns:
        Username o None si el usuario cancela
    """
    message = prompt_message or "Ingresa el username:"
    username = questionary.text(message).ask()
    
    if username:
        username = username.strip()
        if console:
            console.print(f"[green]✓ Username: {username}[/green]")
        return username
    
    return None


def ensure_wlc_profile(
    context: "AppContext",
    console: Optional["Console"] = None
) -> Optional[str]:
    """
    Asegurar que hay un perfil WLC activo. Si falta, lo pide al usuario.
    
    Args:
        context: Contexto de aplicación
        console: Console de Rich (opcional)
        
    Returns:
        Perfil WLC o None si el usuario cancela
    """
    if context.wlc_profile:
        return context.wlc_profile
    
    # Pedir perfil WLC al usuario
    profile = questionary.text("Ingresa el nombre del perfil WLC (o 'skip' para omitir):").ask()
    
    if profile and profile.lower() != "skip":
        context.wlc_profile = profile.strip()
        context.save()
        if console:
            console.print(f"[green]✓ Perfil WLC establecido: {profile}[/green]")
        return context.wlc_profile
    
    return None


def validate_playbook_path(playbook_path: str, base_dir: Optional[Path] = None) -> tuple[bool, Optional[str]]:
    """
    Validar que un playbook existe
    
    Args:
        playbook_path: Ruta al playbook (relativa o absoluta)
        base_dir: Directorio base para rutas relativas (None = directorio actual de ansible)
        
    Returns:
        Tupla (is_valid, error_message)
        - is_valid: True si el playbook existe
        - error_message: Mensaje de error si no existe
    """
    if base_dir is None:
        # Intentar encontrar el directorio base de ansible
        current = Path(__file__).parent.parent.parent
        base_dir = current
    
    # Resolver ruta
    if not Path(playbook_path).is_absolute():
        full_path = base_dir / playbook_path
    else:
        full_path = Path(playbook_path)
    
    if not full_path.exists():
        return False, f"Playbook no encontrado: {playbook_path}"
    
    if not full_path.is_file():
        return False, f"La ruta no es un archivo: {playbook_path}"
    
    if not full_path.suffix == ".yml":
        return False, f"El archivo no es un playbook YAML: {playbook_path}"
    
    return True, None
