import os
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict

# Ajustar path para importar engine y dashboard
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import BackgroundEngine
from dashboard import Dashboard

try:
    import questionary
    from rich.console import Console
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.table import Table
    from rich.text import Text
    from rich import box
except ImportError:
    print("Error: Faltan dependencias. Ejecutar: pip install rich questionary")
    sys.exit(1)

# --- Configuración Base ---
BASE_DIR = Path(__file__).parent.parent.absolute()
os.chdir(BASE_DIR)

console = Console()
engine = BackgroundEngine()
current_target = "localhost"

# Estilo Questionary
CUSTOM_STYLE = questionary.Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:white bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:cyan bold'),
    ('selected', 'fg:green'),
    ('separator', 'fg:gray'),
    ('instruction', 'fg:gray'),
])

# --- Definición simplificada para la demo de Menú ---
MENU_DATA = {
    "🔐 Active Directory": [
        ("Listar Usuarios", "playbooks/admin/list_ad_users.yml"),
        ("Auditar Inactivos", "playbooks/admin/audit_inactive.yml"),
        ("Miembros de Grupo", "playbooks/admin/get_group_members.yml"),
    ],
    "💻 Hardware": [
        ("Test de Performance", "playbooks/hardware/performance_test.yml"),
        ("Inventario Unificado", "playbooks/hardware/unified_inventory.yml"),
        ("Recolección de Logs", "playbooks/hardware/collect_logs.yml"),
    ],
    "📶 Red y WIFI": [
        ("Resetear Adaptador WIFI", "playbooks/network/reset_adapter.yml"),
    ],
    "📦 Software": [
        ("Listar Apps Detallado", "playbooks/software/list_apps_detailed.yml"),
        ("Detectar Shadow IT", "playbooks/software/detect_shadow_it.yml"),
    ],
    "🌐 WLC Cisco": [
        ("Ver Lista de APs", "playbooks/wlc/show_ap_list.yml"),
        ("Reporte Telecom", "playbooks/wlc/generate_telecom_report.yml"),
    ]
}

def main_header():
    grid = Table.grid(expand=True)
    grid.add_column(justify="left")
    grid.add_column(justify="right")
    grid.add_row(
        Text(f"🚀 IT-OPS CLI PRO | Target: [bold cyan]{current_target}[/bold cyan]", style="white"),
        Text(f"Jobs Activos: {len([j for j in engine.get_all_jobs() if j['status'] == 'RUNNING'])}", style="yellow")
    )
    return Panel(grid, style="bg:blue fg:white")

def change_target():
    global current_target
    new_target = questionary.text("Ingresa el nuevo Hostname/IP target:", style=CUSTOM_STYLE).ask()
    if new_target:
        current_target = new_target.upper()

def launch_task():
    # 1. Seleccionar Categoría
    cat = questionary.select(
        "Selecciona Categoría:",
        choices=list(MENU_DATA.keys()) + ["⬅️ Volver"],
        style=CUSTOM_STYLE
    ).ask()

    if cat == "⬅️ Volver" or not cat:
        return

    # 2. Seleccionar Playbook
    options = MENU_DATA[cat]
    choice = questionary.select(
        f"Lanzar tarea en {current_target}:",
        choices=[o[0] for o in options] + ["⬅️ Volver"],
        style=CUSTOM_STYLE
    ).ask()

    if choice == "⬅️ Volver" or not choice:
        return

    # Encontrar el path del playbook
    playbook_path = next(o[1] for o in options if o[0] == choice)
    
    # Lanzar!
    job_id = engine.launch_playbook(playbook_path, current_target)
    console.print(f"[bold green]✔ Tarea lanzada con ID: {job_id}[/bold green]")
    time.sleep(1)

def main_menu():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(main_header())
        
        action = questionary.select(
            "¿Qué deseas hacer?",
            choices=[
                "🚀 Lanzar Nueva Tarea",
                "📊 Ver Dashboard de Tareas (Segundo Plano)",
                "🎯 Cambiar Equipo Target",
                "❌ Salir"
            ],
            style=CUSTOM_STYLE
        ).ask()

        if action == "🚀 Lanzar Nueva Tarea":
            launch_task()
        elif action == "📊 Ver Dashboard de Tareas (Segundo Plano)":
            db = Dashboard(engine)
            db.show_live() # Esto entra en el modo interactivo del dashboard
        elif action == "🎯 Cambiar Equipo Target":
            change_target()
        elif action == "❌ Salir":
            break

if __name__ == "__main__":
    main_menu()
