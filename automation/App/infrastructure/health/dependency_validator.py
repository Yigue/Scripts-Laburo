"""
DependencyValidator - Validación de dependencias de la aplicación
"""
import sys
import importlib
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class DependencyCheck:
    """Resultado de verificación de una dependencia"""
    name: str
    required: bool
    installed: bool
    version: str = ""
    error: str = ""


class DependencyValidator:
    """Validador de dependencias de la aplicación"""
    
    def __init__(self):
        """Inicializa el validador"""
        self.checks: List[DependencyCheck] = []
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Valida todas las dependencias
        
        Returns:
            Dict con resultados de validación
        """
        print("\n🔍 Verificando dependencias...")
        print("=" * 60)
        
        # Python version
        self._check_python_version()
        
        # Librerías Python
        self._check_library("pypsrp", required=True)
        self._check_library("pypsexec", required=True)
        self._check_library("ansible", required=False)
        self._check_library("colorama", required=False)
        
        # Mostrar resultados
        self._print_results()
        
        # Retornar summary
        installed = sum(1 for c in self.checks if c.installed)
        required_missing = [c for c in self.checks if c.required and not c.installed]
        
        return {
            "total_checks": len(self.checks),
            "installed": installed,
            "missing": len(self.checks) - installed,
            "required_missing": len(required_missing),
            "all_required_met": len(required_missing) == 0,
            "checks": self.checks
        }
    
    def _check_python_version(self):
        """Verifica versión de Python"""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        is_valid = version.major == 3 and version.minor >= 8
        
        check = DependencyCheck(
            name="Python",
            required=True,
            installed=is_valid,
            version=version_str,
            error="" if is_valid else "Se requiere Python 3.8+"
        )
        self.checks.append(check)
    
    def _check_library(self, library_name: str, required: bool = True):
        """
        Verifica si una librería está instalada
        
        Args:
            library_name: Nombre de la librería
            required: Si es requerida
        """
        try:
            module = importlib.import_module(library_name)
            version = getattr(module, '__version__', 'unknown')
            
            check = DependencyCheck(
                name=library_name,
                required=required,
                installed=True,
                version=version
            )
        except ImportError as e:
            check = DependencyCheck(
                name=library_name,
                required=required,
                installed=False,
                error=str(e)
            )
        
        self.checks.append(check)
    
    def _print_results(self):
        """Imprime resultados de validación"""
        for check in self.checks:
            status = "✅" if check.installed else ("❌" if check.required else "⚠️")
            req_text = "(Requerido)" if check.required else "(Opcional)"
            version_text = f"v{check.version}" if check.version else ""
            
            print(f"{status} {check.name:15} {req_text:15} {version_text}")
            
            if not check.installed and check.error:
                print(f"   └─ {check.error}")
        
        print("=" * 60)

