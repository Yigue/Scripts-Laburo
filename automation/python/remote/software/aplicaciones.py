"""
Módulo para gestión de aplicaciones instaladas
Corresponde a la opción 11 del menú
"""
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)
from utils.remote_executor import RemoteExecutor


SCRIPT_LISTAR_APPS = '''
function Get-InstalledApplications {
    param ([string]$RegistryPath)
    
    Get-ItemProperty -Path $RegistryPath -ErrorAction SilentlyContinue | ForEach-Object {
        $_ | Select-Object @{
            Name       = 'Name'
            Expression = { $_.DisplayName }
        }, @{
            Name       = 'Version'
            Expression = { $_.DisplayVersion }
        }, @{
            Name       = 'Publisher'
            Expression = { $_.Publisher }
        }, @{
            Name       = 'UninstallString'
            Expression = { $_.UninstallString }
        }
    } | Where-Object { $_.Name -ne $null }
}

$RegistryPaths = @(
    "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*",
    "HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*"
)

# Obtener todas las apps
$Applications = foreach ($Path in $RegistryPaths) {
    Get-InstalledApplications -RegistryPath $Path
}

# Ordenar y numerar
$Applications = $Applications | Sort-Object Name | Select-Object -Unique Name, Version, Publisher, UninstallString

$index = 0
$output = @()
foreach ($app in $Applications) {
    $output += [PSCustomObject]@{
        Index = $index
        Name = $app.Name
        Version = $app.Version
        Publisher = $app.Publisher
    }
    $index++
}

$output | Format-Table Index, Name, Version, Publisher -AutoSize

# Guardar para referencia
$Applications | Export-Clixml -Path "C:\\TEMP\\apps_list.xml" -Force

Write-Host ""
Write-Host "Total: $($Applications.Count) aplicaciones" -ForegroundColor Cyan
'''


def get_script_uninstall(app_index: int):
    """
    Genera script para desinstalar aplicación por índice
    """
    return f'''
$apps = Import-Clixml -Path "C:\\TEMP\\apps_list.xml"
$index = {app_index}

if ($index -lt 0 -or $index -ge $apps.Count) {{
    Write-Host "Indice invalido" -ForegroundColor Red
    return
}}

$app = $apps[$index]
Write-Host "Desinstalando: $($app.Name)" -ForegroundColor Yellow

$uninstallCmd = $app.UninstallString

if (-not $uninstallCmd) {{
    Write-Host "No se encontro comando de desinstalacion para esta aplicacion" -ForegroundColor Red
    return
}}

Write-Host "Comando: $uninstallCmd" -ForegroundColor Gray

try {{
    if ($uninstallCmd -like "msiexec*") {{
        # Extraer GUID si es MSI
        if ($uninstallCmd -match "\\{{[A-F0-9-]+\\}}") {{
            $guid = $Matches[0]
            Start-Process "msiexec.exe" -ArgumentList "/x $guid /quiet /norestart" -Wait -NoNewWindow
        }} else {{
            Start-Process "cmd.exe" -ArgumentList "/c $uninstallCmd /quiet /norestart" -Wait -NoNewWindow
        }}
    }} else {{
        # Para otros instaladores
        Start-Process "cmd.exe" -ArgumentList "/c `"$uninstallCmd`" /S /silent" -Wait -NoNewWindow
    }}
    
    Write-Host "Proceso de desinstalacion iniciado" -ForegroundColor Green
}} catch {{
    Write-Host "Error: $_" -ForegroundColor Red
}}
'''


SCRIPT_BUSCAR_APP = '''
param([string]$SearchTerm)

function Get-InstalledApplications {
    param ([string]$RegistryPath)
    
    Get-ItemProperty -Path $RegistryPath -ErrorAction SilentlyContinue | ForEach-Object {
        $_ | Select-Object DisplayName, DisplayVersion, Publisher, UninstallString
    } | Where-Object { $_.DisplayName -ne $null }
}

$RegistryPaths = @(
    "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*",
    "HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*"
)

$Applications = foreach ($Path in $RegistryPaths) {
    Get-InstalledApplications -RegistryPath $Path
}

$filtered = $Applications | Where-Object { 
    $_.DisplayName -like "*$SearchTerm*" -or $_.Publisher -like "*$SearchTerm*" 
} | Sort-Object DisplayName | Select-Object -Unique DisplayName, DisplayVersion, Publisher

if ($filtered) {
    $filtered | Format-Table -AutoSize
    Write-Host "Encontradas: $($filtered.Count) aplicaciones" -ForegroundColor Cyan
} else {
    Write-Host "No se encontraron aplicaciones con '$SearchTerm'" -ForegroundColor Yellow
}
'''


def ejecutar(executor: RemoteExecutor, hostname: str):
    """
    Menú de gestión de aplicaciones
    
    Args:
        executor: Instancia de RemoteExecutor
        hostname: Nombre del equipo remoto
    """
    while True:
        print(f"\n📦 Gestión de Aplicaciones en {hostname}")
        print()
        print("1. Listar todas las aplicaciones")
        print("2. Buscar aplicación")
        print("3. Desinstalar aplicación")
        print("0. Volver")
        print()
        
        opcion = input("Seleccioná una opción: ").strip()
        
        if opcion == "1":
            print(f"\n📋 Listando aplicaciones de {hostname}...")
            print("   (Esto puede tomar unos segundos)")
            print()
            
            result = executor.run_script_block(hostname, SCRIPT_LISTAR_APPS, timeout=60)
            if result:
                print(result)
            else:
                print("❌ Error obteniendo lista de aplicaciones")
            
            input("\nPresioná ENTER para continuar...")
        
        elif opcion == "2":
            search_term = input("\nBuscar: ").strip()
            if not search_term:
                continue
            
            print(f"\n🔍 Buscando '{search_term}'...")
            
            # Construir script con parámetro
            script = f'''
$SearchTerm = "{search_term}"
''' + SCRIPT_BUSCAR_APP.replace('param([string]$SearchTerm)', '')
            
            result = executor.run_script_block(hostname, script, timeout=30)
            if result:
                print(result)
            else:
                print("❌ Error en la búsqueda")
            
            input("\nPresioná ENTER para continuar...")
        
        elif opcion == "3":
            # Primero listar
            print(f"\n📋 Listando aplicaciones...")
            result = executor.run_script_block(hostname, SCRIPT_LISTAR_APPS, timeout=60)
            if result:
                print(result)
            else:
                print("❌ Error obteniendo lista")
                continue
            
            # Pedir índice
            index_str = input("\nNúmero de aplicación a desinstalar (o ENTER para cancelar): ").strip()
            if not index_str:
                continue
            
            try:
                index = int(index_str)
            except ValueError:
                print("❌ Número inválido")
                continue
            
            # Confirmar
            confirmar = input(f"¿Confirmar desinstalación del índice {index}? (S/N): ").strip().upper()
            if confirmar != "S":
                continue
            
            # Ejecutar desinstalación
            print(f"\n🗑️ Desinstalando...")
            script = get_script_uninstall(index)
            result = executor.run_script_block(hostname, script, timeout=120)
            if result:
                print(result)
            
            input("\nPresioná ENTER para continuar...")
        
        elif opcion == "0":
            break
        else:
            print("Opción inválida")


def main():
    """Función principal para ejecución standalone"""
    from utils.common import clear_screen
    
    clear_screen()
    print("=" * 60)
    print("📦 GESTIÓN DE APLICACIONES")
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

