"""
ScriptLoader - Carga scripts PowerShell desde archivos
"""
from pathlib import Path
from typing import Optional
from shared.exceptions import ScriptLoadError
from domain.interfaces import IScriptLoader


class ScriptLoader(IScriptLoader):
    """
    Carga scripts PowerShell desde archivos .ps1
    Elimina la necesidad de embeber scripts en strings Python
    """
    
    def __init__(self, scripts_base_dir: str = "automation/scripts"):
        """
        Inicializa el script loader
        
        Args:
            scripts_base_dir: Directorio base donde están los scripts
        """
        self.scripts_dir = Path(scripts_base_dir)
        
        if not self.scripts_dir.exists():
            raise ScriptLoadError(f"Directorio de scripts no encontrado: {scripts_base_dir}")
    
    def load(self, category: str, script_name: str) -> str:
        """
        Carga un script PowerShell desde archivo
        
        Args:
            category: Categoría (hardware, software, network, common, etc)
            script_name: Nombre del script (sin extensión .ps1)
            
        Returns:
            str: Contenido del script
            
        Raises:
            ScriptLoadError: Si el script no se encuentra o no se puede leer
            
        Example:
            loader = ScriptLoader()
            script = loader.load("hardware", "get_system_info")
        """
        # Agregar extensión si no la tiene
        if not script_name.endswith('.ps1'):
            script_name += '.ps1'
        
        script_path = self.scripts_dir / category / script_name
        
        if not script_path.exists():
            raise ScriptLoadError(f"Script no encontrado: {script_path}")
        
        try:
            return script_path.read_text(encoding='utf-8')
        except Exception as e:
            raise ScriptLoadError(f"Error leyendo script {script_path}: {e}")
    
    def load_with_wrapper(self, category: str, script_name: str) -> str:
        """
        Carga script con wrapper de error handling
        Incluye redirección de Write-Host y try-catch
        
        Args:
            category: Categoría del script
            script_name: Nombre del script
            
        Returns:
            str: Script completo con wrappers
        """
        # Cargar script de redirección Write-Host
        try:
            redirect_script = self.load("common", "write_host_redirect")
        except ScriptLoadError:
            # Si no existe, usar versión hardcoded
            redirect_script = """# Redirigir Write-Host a Write-Output
function Write-Host {
    param([string]$Object, [string]$ForegroundColor, [string]$BackgroundColor)
    Write-Output $Object
}
$null = $true"""
        
        # Cargar script principal
        main_script = self.load(category, script_name)
        
        # Construir script completo
        wrapped_script = f"""{redirect_script}

Write-Output ">>> INICIO DEL SCRIPT <<<"

try {{
{self._indent_script(main_script, 4)}
}} catch {{
    Write-Output "❌ ERROR: $($_.Exception.Message)"
    Write-Output "StackTrace: $($_.ScriptStackTrace)"
    throw
}}

Write-Output ">>> FIN DEL SCRIPT <<<"
"""
        return wrapped_script
    
    def _indent_script(self, script: str, spaces: int = 4) -> str:
        """Indenta un script con el número de espacios especificado"""
        indent = " " * spaces
        lines = script.split('\n')
        return '\n'.join(indent + line if line.strip() else line for line in lines)
    
    def script_exists(self, category: str, script_name: str) -> bool:
        """
        Verifica si un script existe
        
        Args:
            category: Categoría del script
            script_name: Nombre del script
            
        Returns:
            bool: True si el script existe
        """
        if not script_name.endswith('.ps1'):
            script_name += '.ps1'
        
        script_path = self.scripts_dir / category / script_name
        return script_path.exists()
    
    def list_scripts(self, category: str) -> list:
        """
        Lista todos los scripts disponibles en una categoría
        
        Args:
            category: Categoría a listar
            
        Returns:
            list: Lista de nombres de scripts (sin extensión)
        """
        category_dir = self.scripts_dir / category
        
        if not category_dir.exists():
            return []
        
        scripts = []
        for script_file in category_dir.glob("*.ps1"):
            scripts.append(script_file.stem)  # nombre sin extensión
        
        return sorted(scripts)

