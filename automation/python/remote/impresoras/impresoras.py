"""
Módulo para instalar impresoras (Lexmark y Zebra)
Corresponde a la opción 9 del menú
"""
import sys
import os
import shutil

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)
from utils.remote_executor import RemoteExecutor


# Rutas de drivers
LEXMARK_DRIVER_SOURCE = r"\\pc101338\c$\iTools\Drivers-IMs\Lexmark\lmud1n40.inf"
ZEBRA_DRIVER_SOURCE = r"\\pc101338\c$\iTools\Drivers-IMs\Zebras\ZBRN.inf"


def get_script_install_printer(driver_inf: str, driver_name: str, printer_name: str, ip_address: str):
    """
    Genera el script de instalación de impresora
    """
    return f'''
$driverInf = "{driver_inf}"
$driverName = "{driver_name}"
$printerName = "{printer_name}"
$ipAddress = "{ip_address}"

Write-Host "=========================================="
Write-Host "     INSTALACION DE IMPRESORA"
Write-Host "=========================================="
Write-Host ""

# Verificar driver
if (-not (Test-Path $driverInf)) {{
    Write-Host "Error: Archivo INF no encontrado: $driverInf" -ForegroundColor Red
    return
}}

# Instalar driver
Write-Host "Instalando driver..." -ForegroundColor Yellow
try {{
    pnputil /add-driver $driverInf /install 2>&1 | Out-Null
    Write-Host "   Driver instalado" -ForegroundColor Green
}} catch {{
    Write-Host "   Error instalando driver: $_" -ForegroundColor Red
}}

Start-Sleep -Seconds 3

# Registrar driver
Write-Host "Registrando driver..." -ForegroundColor Yellow
$existingDriver = Get-PrinterDriver -Name $driverName -ErrorAction SilentlyContinue
if (-not $existingDriver) {{
    try {{
        Add-PrinterDriver -Name $driverName -ErrorAction Stop
        Write-Host "   Driver registrado" -ForegroundColor Green
    }} catch {{
        # Intentar con printui
        rundll32 printui.dll,PrintUIEntry /ia /m "$driverName" /f "$driverInf"
        Start-Sleep -Seconds 3
    }}
}} else {{
    Write-Host "   Driver ya registrado" -ForegroundColor Green
}}

# Crear puerto TCP/IP
Write-Host "Creando puerto TCP/IP..." -ForegroundColor Yellow
$existingPort = Get-PrinterPort -Name $ipAddress -ErrorAction SilentlyContinue
if (-not $existingPort) {{
    try {{
        Add-PrinterPort -Name $ipAddress -PrinterHostAddress $ipAddress -ErrorAction Stop
        Write-Host "   Puerto creado: $ipAddress" -ForegroundColor Green
    }} catch {{
        Write-Host "   Error creando puerto: $_" -ForegroundColor Red
        return
    }}
}} else {{
    Write-Host "   Puerto ya existe" -ForegroundColor Green
}}

# Agregar impresora
Write-Host "Agregando impresora..." -ForegroundColor Yellow
$existingPrinter = Get-Printer -Name $printerName -ErrorAction SilentlyContinue
if (-not $existingPrinter) {{
    try {{
        Add-Printer -Name $printerName -DriverName $driverName -PortName $ipAddress -ErrorAction Stop
        Write-Host "   Impresora agregada: $printerName" -ForegroundColor Green
    }} catch {{
        Write-Host "   Error agregando impresora: $_" -ForegroundColor Red
        return
    }}
}} else {{
    Write-Host "   La impresora ya existe" -ForegroundColor Yellow
}}

Write-Host ""
Write-Host "=========================================="
Write-Host "     INSTALACION COMPLETADA"
Write-Host "=========================================="
'''


def copiar_driver(hostname: str, driver_source: str, driver_name: str, verbose: bool = True):
    """
    Copia el driver de impresora al equipo remoto
    
    Args:
        hostname: Nombre del equipo remoto
        driver_source: Ruta del driver origen
        driver_name: Nombre del archivo destino
        verbose: Si True, muestra mensajes
    
    Returns:
        str: Ruta destino del driver o None si falla
    """
    destino_remoto = f"\\\\{hostname}\\c$"
    dest_file = os.path.join(destino_remoto, driver_name)
    
    try:
        if verbose:
            print(f"📦 Copiando driver {driver_name}...")
        
        if os.path.exists(driver_source):
            shutil.copy2(driver_source, dest_file)
            if verbose:
                print(f"   ✅ Driver copiado")
            return f"C:\\{driver_name}"
        else:
            if verbose:
                print(f"   ❌ No se encontró: {driver_source}")
            return None
            
    except Exception as e:
        if verbose:
            print(f"❌ Error copiando driver: {e}")
        return None


def instalar_lexmark(executor: RemoteExecutor, hostname: str):
    """
    Instala impresora Lexmark
    
    Args:
        executor: Instancia de RemoteExecutor
        hostname: Nombre del equipo remoto
    """
    print("\n🖨️ Instalación de impresora Lexmark")
    print()
    
    # Solicitar datos
    printer_name = input("Nombre de la impresora: ").strip()
    if not printer_name:
        print("❌ Debe ingresar un nombre")
        return
    
    ip_address = input("Dirección IP de la impresora: ").strip()
    if not ip_address:
        print("❌ Debe ingresar una IP")
        return
    
    # Copiar driver
    driver_path = copiar_driver(hostname, LEXMARK_DRIVER_SOURCE, "lmud1n40.inf")
    if not driver_path:
        input("\nPresioná ENTER para continuar...")
        return
    
    # Generar y ejecutar script
    script = get_script_install_printer(
        driver_path,
        "Lexmark Universal v2 PS3",
        printer_name,
        ip_address
    )
    
    print("\n📥 Instalando impresora...")
    result = executor.run_script_block(hostname, script, timeout=120)
    
    if result:
        print(result)
    else:
        print("❌ Error durante la instalación")


def instalar_zebra(executor: RemoteExecutor, hostname: str):
    """
    Instala impresora Zebra WiFi
    
    Args:
        executor: Instancia de RemoteExecutor
        hostname: Nombre del equipo remoto
    """
    print("\n🖨️ Instalación de impresora Zebra WiFi")
    print()
    
    # Solicitar datos
    printer_name = input("Nombre de la impresora: ").strip()
    if not printer_name:
        print("❌ Debe ingresar un nombre")
        return
    
    ip_address = input("Dirección IP de la impresora: ").strip()
    if not ip_address:
        print("❌ Debe ingresar una IP")
        return
    
    # Copiar driver
    driver_path = copiar_driver(hostname, ZEBRA_DRIVER_SOURCE, "ZBRN.inf")
    if not driver_path:
        input("\nPresioná ENTER para continuar...")
        return
    
    # Generar y ejecutar script
    script = get_script_install_printer(
        driver_path,
        "ZDesigner ZD420-203dpi ZPL",
        printer_name,
        ip_address
    )
    
    print("\n📥 Instalando impresora...")
    result = executor.run_script_block(hostname, script, timeout=120)
    
    if result:
        print(result)
    else:
        print("❌ Error durante la instalación")


def ejecutar(executor: RemoteExecutor, hostname: str):
    """
    Menú de instalación de impresoras
    
    Args:
        executor: Instancia de RemoteExecutor
        hostname: Nombre del equipo remoto
    """
    print(f"\n🖨️ Instalación de Impresoras en {hostname}")
    print()
    print("1. Lexmark")
    print("2. Zebra WiFi")
    print("0. Cancelar")
    print()
    
    opcion = input("Seleccioná una opción: ").strip()
    
    if opcion == "1":
        instalar_lexmark(executor, hostname)
    elif opcion == "2":
        instalar_zebra(executor, hostname)
    elif opcion == "0":
        return
    else:
        print("Opción inválida")
    
    print()
    input("Presioná ENTER para continuar...")


def main():
    """Función principal para ejecución standalone"""
    from utils.common import clear_screen
    
    clear_screen()
    print("=" * 60)
    print("🖨️ INSTALAR IMPRESORAS")
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

