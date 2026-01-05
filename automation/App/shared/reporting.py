"""
Módulo de reportes compartido
Genera reportes en formato JSON y TXT
"""
import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

@dataclass
class ReportEntry:
    """Entrada individual de reporte"""
    timestamp: str
    hostname: str
    operation: str
    status: str
    duration: float
    details: str

class ReportGenerator:
    """Clase para generar reportes consolidados"""
    
    def __init__(self, output_dir: str = "data/reports"):
        """
        Inicializa el generador
        
        Args:
            output_dir: Directorio de salida
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_operations_report(self, entries: List[ReportEntry], 
                                  filename: str = None, 
                                  format: str = "json") -> str:
        """
        Genera un reporte de operaciones
        
        Args:
            entries: Lista de entradas
            filename: Nombre opcional
            format: 'json' o 'txt'
            
        Returns:
            Ruta completa del reporte generado
        """
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        filepath = os.path.join(self.output_dir, f"{filename}.{format}")
        
        if format == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([asdict(e) for e in entries], f, indent=4)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"REPORTE DE OPERACIONES - {datetime.now()}\n")
                f.write("=" * 70 + "\n\n")
                for e in entries:
                    f.write(f"[{e.timestamp}] {e.status} - {e.hostname} - {e.operation}\n")
                    if e.details:
                        f.write(f"   Detalles: {e.details}\n")
                    f.write("-" * 40 + "\n")
        
        return filepath
