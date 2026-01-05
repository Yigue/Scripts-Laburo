"""
Modelos de Resultado - Representación de resultados de operaciones
"""
from dataclasses import dataclass, field
from typing import Optional, Any, Dict
from datetime import datetime


@dataclass
class Result:
    """Resultado de ejecución de comando/script remoto"""
    
    success: bool
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    method_used: str = "unknown"  # 'winrm', 'psexec', 'ansible'
    error: Optional[str] = None
    execution_time: float = 0.0  # segundos
    
    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"Result({status}, method={self.method_used}, time={self.execution_time:.2f}s)"
    
    @property
    def output(self) -> str:
        """Retorna stdout + stderr combinados"""
        if self.stdout and self.stderr:
            return f"{self.stdout}\n{self.stderr}"
        return self.stdout or self.stderr or ""


@dataclass
class OperationResult:
    """Resultado de una operación de alto nivel (caso de uso)"""
    
    success: bool
    message: str
    data: Optional[Any] = None
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"OperationResult({status}: {self.message})"
    
    def add_error(self, error: str):
        """Agrega un error a la lista"""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str):
        """Agrega una advertencia"""
        self.warnings.append(warning)
    
    @property
    def has_warnings(self) -> bool:
        """Verifica si hay advertencias"""
        return len(self.warnings) > 0
    
    @property
    def has_errors(self) -> bool:
        """Verifica si hay errores"""
        return len(self.errors) > 0

