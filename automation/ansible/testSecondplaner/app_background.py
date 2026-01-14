from engine import BackgroundEngine
from dashboard import Dashboard
from rich.console import Console
import time
import os

console = Console()

def run_pro_demo():
    engine = BackgroundEngine()
    db = Dashboard(engine)

    console.print(Panel.fit("[bold blue]IT-OPS CLI: Professional Background Engine[/bold blue]\n[dim]Iniciando sistema de gestión de tareas asíncronas...[/dim]", border_style="blue"))
    
    # Lista de playbooks para la demo (usando los reales creados anteriormente)
    playbooks = [
        ("playbooks/admin/list_ad_users.yml", "DC-PROD-01"),
        ("playbooks/hardware/performance_test.yml", "WKST-LT-99"),
        ("playbooks/sccm/list_devices.yml", "SCCM-SRV"),
        ("playbooks/monitoring/health_checks.yml", "SRV-FILE-01")
    ]

    with console.status("[bold green]Lanzando playbooks iniciales...") as status:
        for pb, host in playbooks:
            full_path = os.path.join(os.getcwd(), pb)
            if os.path.exists(full_path):
                job_id = engine.launch_playbook(full_path, host)
                console.log(f"[green]Job {job_id}[/green] lanzado para [cyan]{pb}[/cyan]")
                time.sleep(0.5) # Breve pausa para efecto visual
            else:
                console.log(f"[red]Error:[/red] No se encontró {pb}")

    console.print("\n[bold yellow]Accediendo al panel de control interactivo...[/bold yellow]")
    time.sleep(1.5)
    
    # Lanzamos el dashboard profesional
    db.show_live()

if __name__ == "__main__":
    from rich.panel import Panel
    run_pro_demo()
