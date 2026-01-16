"""
Ejecutores CLI para modo rápido
"""
import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console

from core.context import AppContext
from core.engine import BackgroundEngine
from core.validators import validate_playbook_path
from core.risk_gating import validate_read_only


class CLIExecutor:
    """Ejecutor para comandos CLI rápidos"""
    
    def __init__(self):
        self.context = AppContext()
        self.engine = BackgroundEngine()
        self.console = Console()
        self.base_dir = Path(__file__).parent.parent.parent.parent
    
    def execute(self, action: Dict[str, Any]) -> int:
        """
        Ejecutar acción desde CLI
        
        Args:
            action: Diccionario con información de la acción
            
        Returns:
            Exit code (0 = éxito, 1 = error)
        """
        playbook_path = action.get("playbook")
        if not playbook_path:
            self.console.print("[red]Error: No se especificó playbook[/red]", file=sys.stderr)
            return 1
        
        # Validar playbook
        is_valid, error_msg = validate_playbook_path(playbook_path, self.base_dir)
        if not is_valid:
            self.console.print(f"[red]Error: {error_msg}[/red]", file=sys.stderr)
            return 1
        
        # Validar read-only si está forzado
        if action.get("read_only"):
            action_metadata = {
                "action_type": action.get("action_type", "read-only"),
                "name": action.get("name", "Acción CLI")
            }
            is_allowed, error_msg = validate_read_only(action_metadata, self.context)
            if not is_allowed:
                self.console.print(error_msg, file=sys.stderr)
                return 1
        
        # Obtener target
        target = action.get("target")
        if action.get("requires_target") and not target:
            self.console.print("[red]Error: Se requiere --host[/red]", file=sys.stderr)
            return 1
        
        target = target or "localhost"
        
        # Construir comando ansible-playbook
        cmd = [
            "ansible-playbook",
            playbook_path,
            "-i", "inventory/hosts.ini",
            "-e", f"target_host={target}"
        ]
        
        # Agregar check mode
        if action.get("extra_vars", {}).get("check_mode"):
            cmd.append("--check")
        
        # Agregar verbosity
        verbosity = action.get("extra_vars", {}).get("verbosity", 0)
        if verbosity > 0:
            cmd.append("-" + "v" * min(verbosity, 4))
        
        # Agregar extra vars
        extra_vars = action.get("extra_vars", {})
        for k, v in extra_vars.items():
            if k not in ("check_mode", "verbosity"):
                cmd.extend(["-e", f"{k}={v}"])
        
        # Ejecutar síncronamente para CLI
        try:
            if action.get("output_json"):
                # Ejecutar y capturar salida para JSON
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(self.base_dir)
                )
                
                output_json = {
                    "success": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "playbook": playbook_path,
                    "target": target
                }
                
                print(json.dumps(output_json, indent=2))
                return result.returncode
            else:
                # Ejecutar y mostrar salida normal
                result = subprocess.run(cmd, cwd=str(self.base_dir))
                return result.returncode
                
        except Exception as e:
            self.console.print(f"[red]Error al ejecutar: {e}[/red]", file=sys.stderr)
            return 1
