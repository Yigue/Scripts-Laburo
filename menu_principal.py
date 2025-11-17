"""
Menú Principal - Automatización IT Andreani
Interfaz centralizada para gestionar todas las herramientas
"""
import os
import sys
import subprocess
import json
from pathlib import Path

# Importar función de búsqueda de PsExec
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'automation', 'python', 'utils'))
try:
    from psexec_helper import find_psexec
except ImportError:
    def find_psexec(path):
        return None if not os.path.isfile(path) else os.path.abspath(path)

# Colores para Windows (usando colorama si está disponible, sino códigos ANSI)
try:
    from colorama import init, Fore, Style
    init()
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    # Códigos ANSI básicos para Windows 10+
    class Fore:
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        RESET = '\033[0m'
    class Style:
        BRIGHT = '\033[1m'
        RESET_ALL = '\033[0m'


def clear_screen():
    """Limpia la pantalla"""
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    """Imprime el encabezado del menú"""
    clear_screen()
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"{' '*15}🔧 AUTOMATIZACIÓN IT - ANDREANI 🔧")
    print(f"{'='*70}{Style.RESET_ALL}{Fore.RESET}")
    print()


def print_menu(options, title="MENÚ PRINCIPAL"):
    """Imprime un menú con opciones"""
    print(f"{Fore.YELLOW}{Style.BRIGHT}╔═══ {title} ═══╗{Style.RESET_ALL}{Fore.RESET}")
    print()
    for i, (key, desc) in enumerate(options.items(), 1):
        print(f"{Fore.CYAN}  {i}.{Fore.RESET} {desc}")
    print()
    print(f"{Fore.YELLOW}  0.{Fore.RESET} Salir")
    print()


def get_choice(max_option):
    """Obtiene la elección del usuario"""
    while True:
        try:
            choice = input(f"{Fore.GREEN}➜ Seleccioná una opción: {Fore.RESET}").strip()
            if choice == "0":
                return 0
            choice_num = int(choice)
            if 1 <= choice_num <= max_option:
                return choice_num
            else:
                print(f"{Fore.RED}❌ Opción inválida. Ingresá un número entre 1 y {max_option}{Fore.RESET}")
        except ValueError:
            print(f"{Fore.RED}❌ Ingresá un número válido{Fore.RESET}")
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}👋 ¡Hasta luego!{Fore.RESET}")
            sys.exit(0)


def check_dependencies():
    """Verifica si las dependencias están instaladas"""
    required = ["streamlit", "pandas"]
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing


def install_dependencies():
    """Instala las dependencias faltantes"""
    print(f"\n{Fore.YELLOW}📦 Verificando dependencias...{Fore.RESET}")
    missing = check_dependencies()
    
    if not missing:
        print(f"{Fore.GREEN}✅ Todas las dependencias están instaladas{Fore.RESET}")
        input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")
        return True
    
    print(f"{Fore.YELLOW}⚠️  Faltan las siguientes dependencias: {', '.join(missing)}{Fore.RESET}")
    print(f"{Fore.CYAN}¿Instalar automáticamente? (S/N): {Fore.RESET}", end="")
    response = input().strip().upper()
    
    if response != "S":
        print(f"{Fore.RED}❌ Instalación cancelada{Fore.RESET}")
        input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")
        return False
    
    print(f"\n{Fore.YELLOW}📥 Instalando dependencias...{Fore.RESET}")
    try:
        # Usar python -m pip para evitar problemas con PATH
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"{Fore.GREEN}✅ Dependencias instaladas correctamente{Fore.RESET}")
            input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")
            return True
        else:
            print(f"{Fore.RED}❌ Error al instalar dependencias:{Fore.RESET}")
            print(result.stderr)
            input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")
            return False
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}{Fore.RESET}")
        input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")
        return False


def check_config():
    """Verifica si existe config.json"""
    if os.path.exists("config.json"):
        return True
    
    print(f"\n{Fore.YELLOW}⚠️  No se encontró config.json{Fore.RESET}")
    print(f"{Fore.CYAN}¿Crear archivo de configuración? (S/N): {Fore.RESET}", end="")
    response = input().strip().upper()
    
    if response != "S":
        return False
    
    print(f"\n{Fore.YELLOW}📝 Configurando...{Fore.RESET}")
    psexec_path = input(f"{Fore.CYAN}Ruta a PsExec.exe (Enter para 'PsExec.exe'): {Fore.RESET}").strip() or "PsExec.exe"
    remote_user = input(f"{Fore.CYAN}Usuario remoto (Enter para 'Administrador'): {Fore.RESET}").strip() or "Administrador"
    remote_pass = input(f"{Fore.CYAN}Contraseña remota (Enter para vacío/LAPS): {Fore.RESET}").strip()
    
    config = {
        "psexec_path": psexec_path,
        "remote_user": remote_user,
        "remote_pass": remote_pass,
        "timeout": 30
    }
    
    try:
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        print(f"{Fore.GREEN}✅ Configuración guardada en config.json{Fore.RESET}")
        input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Error al crear config.json: {e}{Fore.RESET}")
        input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")
        return False


def run_script(script_path, description):
    """Ejecuta un script de Python"""
    print(f"\n{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}🚀 {description}{Style.RESET_ALL}{Fore.RESET}")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")
    
    try:
        # Cambiar al directorio del script
        script_dir = os.path.dirname(script_path)
        script_name = os.path.basename(script_path)
        original_dir = os.getcwd()
        
        if script_dir:
            os.chdir(script_dir)
        
        # Ejecutar el script
        result = subprocess.run([sys.executable, script_name])
        
        # Volver al directorio original
        os.chdir(original_dir)
        
        if result.returncode == 0:
            print(f"\n{Fore.GREEN}✅ Script completado{Fore.RESET}")
        else:
            print(f"\n{Fore.YELLOW}⚠️  Script finalizado con código {result.returncode}{Fore.RESET}")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Operación cancelada por el usuario{Fore.RESET}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error al ejecutar script: {e}{Fore.RESET}")
    
    input(f"\n{Fore.CYAN}Presioná ENTER para volver al menú...{Fore.RESET}")


def show_reports():
    """Muestra los reportes disponibles"""
    reports_dir = Path("data/reports")
    
    if not reports_dir.exists():
        print(f"\n{Fore.YELLOW}⚠️  No se encontró el directorio de reportes{Fore.RESET}")
        input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")
        return
    
    report_files = list(reports_dir.glob("*.json"))
    
    if not report_files:
        print(f"\n{Fore.YELLOW}⚠️  No hay reportes disponibles{Fore.RESET}")
        input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")
        return
    
    print(f"\n{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}📊 REPORTES DISPONIBLES{Style.RESET_ALL}{Fore.RESET}")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")
    
    # Agrupar por tipo
    report_types = {}
    for file in sorted(report_files, reverse=True):
        name_parts = file.stem.split("_")
        if len(name_parts) >= 2:
            report_type = "_".join(name_parts[:-2])  # Todo menos fecha y hora
            if report_type not in report_types:
                report_types[report_type] = []
            report_types[report_type].append(file)
    
    for report_type, files in report_types.items():
        print(f"\n{Fore.GREEN}📁 {report_type.upper()}{Fore.RESET}")
        for file in files[:5]:  # Mostrar solo los 5 más recientes
            size = file.stat().st_size / 1024  # KB
            print(f"   • {file.name} ({size:.1f} KB)")
        if len(files) > 5:
            print(f"   ... y {len(files) - 5} más")
    
    input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")


def main_menu():
    """Menú principal"""
    while True:
        print_header()
        
        options = {
            1: "🔧 Scripts de Remediación",
            2: "📡 Análisis Wi-Fi",
            3: "📊 Ver Reportes",
            4: "🌐 Dashboard Web",
            5: "⚙️  Configuración",
            6: "📦 Instalar/Verificar Dependencias",
            7: "🔍 Verificar PsExec",
            8: "📚 Documentación"
        }
        
        print_menu(options)
        choice = get_choice(len(options))
        
        if choice == 0:
            print(f"\n{Fore.YELLOW}👋 ¡Hasta luego!{Fore.RESET}")
            break
        elif choice == 1:
            remediation_menu()
        elif choice == 2:
            wifi_menu()
        elif choice == 3:
            show_reports()
        elif choice == 4:
            dashboard_menu()
        elif choice == 5:
            config_menu()
        elif choice == 6:
            install_dependencies()
        elif choice == 7:
            check_psexec()
        elif choice == 8:
            docs_menu()


def remediation_menu():
    """Menú de scripts de remediación"""
    while True:
        print_header()
        
        options = {
            1: "OneDrive - Reparación automática",
            2: "Outlook - Reparación automática",
            3: "VPN (FortiClient) - Reparación automática",
            4: "SCCM - Reparación del cliente"
        }
        
        print_menu(options, "REMEDIACIÓN")
        choice = get_choice(len(options))
        
        if choice == 0:
            break
        elif choice == 1:
            run_script("automation/python/remediation/onedrive_fix.py", "Reparación de OneDrive")
        elif choice == 2:
            run_script("automation/python/remediation/outlook_fix.py", "Reparación de Outlook")
        elif choice == 3:
            run_script("automation/python/remediation/vpn_fix.py", "Reparación de VPN")
        elif choice == 4:
            run_script("automation/python/remediation/sccm_fix.py", "Reparación de SCCM")


def wifi_menu():
    """Menú de análisis Wi-Fi"""
    while True:
        print_header()
        
        options = {
            1: "Analizar Wi-Fi (recolectar información)",
            2: "Forzar conexión a 5GHz",
            3: "Generar reportes Wi-Fi"
        }
        
        print_menu(options, "WI-FI")
        choice = get_choice(len(options))
        
        if choice == 0:
            break
        elif choice == 1:
            run_script("automation/python/wifi/wifi_analyzer.py", "Análisis de Wi-Fi")
        elif choice == 2:
            run_script("automation/python/wifi/wifi_force_5ghz.py", "Forzar Conexión 5GHz")
        elif choice == 3:
            run_script("automation/python/wifi/wifi_report.py", "Generar Reportes Wi-Fi")


def dashboard_menu():
    """Menú del dashboard"""
    print_header()
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}🌐 DASHBOARD WEB{Style.RESET_ALL}{Fore.RESET}")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")
    
    print(f"{Fore.YELLOW}📊 Iniciando dashboard web...{Fore.RESET}")
    print(f"{Fore.CYAN}El dashboard se abrirá en tu navegador en: http://localhost:8501{Fore.RESET}")
    print(f"{Fore.YELLOW}Presioná Ctrl+C para detener el servidor{Fore.RESET}\n")
    
    try:
        script_path = "automation/python/dashboard/simple_dashboard.py"
        script_dir = os.path.dirname(script_path)
        script_name = os.path.basename(script_path)
        original_dir = os.getcwd()
        
        if script_dir:
            os.chdir(script_dir)
        
        # Verificar si streamlit está instalado
        try:
            import streamlit
        except ImportError:
            print(f"{Fore.RED}❌ Streamlit no está instalado{Fore.RESET}")
            print(f"{Fore.YELLOW}Ejecutá la opción 6 del menú principal para instalar dependencias{Fore.RESET}")
            input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")
            os.chdir(original_dir)
            return
        
        # Ejecutar streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", script_name])
        
        os.chdir(original_dir)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Dashboard detenido{Fore.RESET}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {e}{Fore.RESET}")
    
    input(f"\n{Fore.CYAN}Presioná ENTER para volver al menú...{Fore.RESET}")


def config_menu():
    """Menú de configuración"""
    while True:
        print_header()
        
        options = {
            1: "Ver configuración actual",
            2: "Editar configuración",
            3: "Crear config.json desde ejemplo"
        }
        
        print_menu(options, "CONFIGURACIÓN")
        choice = get_choice(len(options))
        
        if choice == 0:
            break
        elif choice == 1:
            show_config()
        elif choice == 2:
            edit_config()
        elif choice == 3:
            create_config_from_example()


def show_config():
    """Muestra la configuración actual"""
    print(f"\n{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}⚙️  CONFIGURACIÓN ACTUAL{Style.RESET_ALL}{Fore.RESET}")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")
    
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            
            print(f"{Fore.GREEN}✅ Archivo config.json encontrado{Fore.RESET}\n")
            for key, value in config.items():
                if key == "remote_pass":
                    display_value = "***" if value else "(vacío/LAPS)"
                else:
                    display_value = value
                print(f"   {Fore.CYAN}{key}:{Fore.RESET} {display_value}")
        except Exception as e:
            print(f"{Fore.RED}❌ Error al leer config.json: {e}{Fore.RESET}")
    else:
        print(f"{Fore.YELLOW}⚠️  No se encontró config.json{Fore.RESET}")
        print(f"{Fore.CYAN}Usando valores por defecto{Fore.RESET}")
    
    input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")


def edit_config():
    """Edita la configuración"""
    if not os.path.exists("config.json"):
        print(f"\n{Fore.YELLOW}⚠️  No existe config.json. Creá uno primero.{Fore.RESET}")
        input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")
        return
    
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error al leer config.json: {e}{Fore.RESET}")
        input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")
        return
    
    print(f"\n{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}✏️  EDITAR CONFIGURACIÓN{Style.RESET_ALL}{Fore.RESET}")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")
    
    psexec_path = input(f"{Fore.CYAN}Ruta a PsExec.exe [{config.get('psexec_path', 'PsExec.exe')}]: {Fore.RESET}").strip()
    if psexec_path:
        config["psexec_path"] = psexec_path
    
    remote_user = input(f"{Fore.CYAN}Usuario remoto [{config.get('remote_user', 'Administrador')}]: {Fore.RESET}").strip()
    if remote_user:
        config["remote_user"] = remote_user
    
    remote_pass = input(f"{Fore.CYAN}Contraseña remota (Enter para mantener actual): {Fore.RESET}").strip()
    if remote_pass:
        config["remote_pass"] = remote_pass
    
    try:
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        print(f"\n{Fore.GREEN}✅ Configuración guardada{Fore.RESET}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error al guardar: {e}{Fore.RESET}")
    
    input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")


def create_config_from_example():
    """Crea config.json desde el ejemplo"""
    if os.path.exists("config.json"):
        print(f"\n{Fore.YELLOW}⚠️  config.json ya existe{Fore.RESET}")
        print(f"{Fore.CYAN}¿Sobrescribir? (S/N): {Fore.RESET}", end="")
        if input().strip().upper() != "S":
            return
    
    check_config()


def docs_menu():
    """Menú de documentación"""
    while True:
        print_header()
        
        options = {
            1: "README Principal",
            2: "Guía de WinRM",
            3: "Guía de Pruebas",
            4: "Documentación de Ansible"
        }
        
        print_menu(options, "DOCUMENTACIÓN")
        choice = get_choice(len(options))
        
        if choice == 0:
            break
        elif choice == 1:
            show_file("README.md")
        elif choice == 2:
            show_file("automation/WINRM_SETUP.md")
        elif choice == 3:
            show_file("automation/TESTING.md")
        elif choice == 4:
            show_file("automation/ansible/README.md")


def check_psexec():
    """Verifica si PsExec está disponible"""
    print_header()
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}🔍 VERIFICACIÓN DE PSEXEC{Style.RESET_ALL}{Fore.RESET}")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")
    
    # Cargar configuración
    config = {}
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
        except:
            pass
    
    psexec_path = config.get("psexec_path", "PsExec.exe")
    
    print(f"{Fore.CYAN}Buscando PsExec.exe...{Fore.RESET}\n")
    print(f"{Fore.YELLOW}Ruta configurada: {psexec_path}{Fore.RESET}\n")
    
    # Buscar PsExec
    found_path = find_psexec(psexec_path)
    
    if found_path:
        print(f"{Fore.GREEN}✅ PsExec encontrado!{Fore.RESET}\n")
        print(f"   Ruta: {found_path}\n")
        
        # Verificar que sea ejecutable
        if os.access(found_path, os.X_OK):
            print(f"{Fore.GREEN}✅ El archivo es ejecutable{Fore.RESET}\n")
        else:
            print(f"{Fore.YELLOW}⚠️  El archivo existe pero podría no ser ejecutable{Fore.RESET}\n")
        
        # Mostrar tamaño
        try:
            size = os.path.getsize(found_path) / 1024  # KB
            print(f"   Tamaño: {size:.1f} KB\n")
        except:
            pass
        
        print(f"{Fore.GREEN}✅ Todo listo para usar los scripts de automatización!{Fore.RESET}\n")
    else:
        print(f"{Fore.RED}❌ PsExec.exe no encontrado{Fore.RESET}\n")
        print(f"{Fore.YELLOW}Ubicaciones buscadas:{Fore.RESET}")
        print(f"   • {os.path.abspath(psexec_path)}")
        print(f"   • {os.path.join(os.getcwd(), 'PsExec.exe')}")
        print(f"   • PATH del sistema")
        print(f"   • C:\\PSTools\\PsExec.exe")
        print(f"   • C:\\Sysinternals\\PsExec.exe")
        print(f"   • C:\\Tools\\PsExec.exe")
        print(f"   • {os.path.join(os.path.expanduser('~'), 'Downloads', 'PsExec.exe')}\n")
        
        print(f"{Fore.CYAN}Soluciones:{Fore.RESET}")
        print(f"   1. Descargá PsExec de:")
        print(f"      {Fore.BLUE}https://docs.microsoft.com/en-us/sysinternals/downloads/psexec{Fore.RESET}")
        print(f"   2. Colocalo en una de estas ubicaciones:")
        print(f"      • Directorio del script: {os.getcwd()}")
        print(f"      • C:\\PSTools\\ (recomendado)")
        print(f"      • C:\\Sysinternals\\")
        print(f"      • C:\\Tools\\")
        print(f"   3. O especificá la ruta completa en config.json\n")
    
    input(f"{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")


def show_file(filepath):
    """Muestra el contenido de un archivo"""
    if not os.path.exists(filepath):
        print(f"\n{Fore.RED}❌ Archivo no encontrado: {filepath}{Fore.RESET}")
        input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")
        return
    
    print(f"\n{Fore.CYAN}{'='*70}{Fore.RESET}")
    print(f"{Fore.YELLOW}{Style.BRIGHT}📄 {filepath}{Style.RESET_ALL}{Fore.RESET}")
    print(f"{Fore.CYAN}{'='*70}{Fore.RESET}\n")
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        print(content)
    except Exception as e:
        print(f"{Fore.RED}❌ Error al leer archivo: {e}{Fore.RESET}")
    
    input(f"\n{Fore.CYAN}Presioná ENTER para continuar...{Fore.RESET}")


if __name__ == "__main__":
    try:
        # Verificar y crear directorios necesarios
        os.makedirs("data/logs", exist_ok=True)
        os.makedirs("data/reports", exist_ok=True)
        
        # Verificar dependencias básicas al inicio
        missing = check_dependencies()
        if missing:
            print(f"\n{Fore.YELLOW}⚠️  Algunas dependencias faltan: {', '.join(missing)}{Fore.RESET}")
            print(f"{Fore.CYAN}Podés instalarlas desde el menú principal (opción 6){Fore.RESET}\n")
        
        main_menu()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 ¡Hasta luego!{Fore.RESET}")
        sys.exit(0)

