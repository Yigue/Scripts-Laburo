"""
Módulo para activar licencia de Windows
Corresponde a la opción 7 del menú
"""
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)
from utils.remote_executor import RemoteExecutor


# Claves de licencia (MAK o KMS)
SCRIPT_ACTIVAR_WINDOWS = '''
Write-Host "=========================================="
Write-Host "     ACTIVACION DE WINDOWS"
Write-Host "=========================================="
Write-Host ""

$keys = @(
    "P9BHN-HYVGH-DVK3V-JHPJ6-HFR9M",
    "3BRT8-N267D-TXT8G-W2F7F-JHW4K",
    "22JFY-NPQ9G-RQ6P2-9PYM7-2R6FT"
)

$activated = $false

foreach ($key in $keys) {
    Write-Host "Intentando con clave: $($key.Substring(0,5))..." -ForegroundColor Yellow
    
    $result = cscript //nologo C:\\Windows\\System32\\slmgr.vbs /ipk $key 2>&1
    
    if ($result -match "correctamente|successfully") {
        Write-Host "   Clave instalada" -ForegroundColor Green
        $activated = $true
        break
    } else {
        Write-Host "   Esta clave no funciono" -ForegroundColor Gray
    }
}

if ($activated) {
    Write-Host ""
    Write-Host "Activando Windows..." -ForegroundColor Yellow
    $activateResult = cscript //nologo C:\\Windows\\System32\\slmgr.vbs /ato 2>&1
    Write-Host $activateResult
    
    Write-Host ""
    Write-Host "Estado de activacion:" -ForegroundColor Cyan
    cscript //nologo C:\\Windows\\System32\\slmgr.vbs /xpr
} else {
    Write-Host ""
    Write-Host "Ninguna clave funciono" -ForegroundColor Red
    Write-Host "Puede ser necesario contactar a sistemas para obtener una clave valida"
}

Write-Host ""
Write-Host "=========================================="
'''


def ejecutar(executor: RemoteExecutor, hostname: str):
    """
    Activa la licencia de Windows en el equipo remoto
    
    Args:
        executor: Instancia de RemoteExecutor
        hostname: Nombre del equipo remoto
    """
    print(f"\n🔑 Activando Windows en {hostname}...")
    print()
    
    result = executor.run_script_block(hostname, SCRIPT_ACTIVAR_WINDOWS, timeout=60)
    
    if result:
        print(result)
    else:
        print("❌ Error activando Windows")
    
    print()
    input("Presioná ENTER para continuar...")


def main():
    """Función principal para ejecución standalone"""
    from utils.common import clear_screen
    
    clear_screen()
    print("=" * 60)
    print("🔑 ACTIVAR WINDOWS")
    print("=" * 60)
    
    hostname = input("\nInventario: ").strip()
    if not hostname:
        print("❌ Debe ingresar un inventario")
        return
    
    executor = RemoteExecutor()
    
    conn = executor.test_connection(hostname)
    if not conn["ready"]:
        print(f"\n❌ No se pudo conectar a {hostname}")
        input("\nPresioná ENTER para salir...")
        return
    
    ejecutar(executor, hostname)


if __name__ == "__main__":
    main()

