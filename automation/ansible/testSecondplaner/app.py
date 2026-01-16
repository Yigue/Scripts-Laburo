#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IT-Ops CLI - Herramienta de Automatización con Ansible (Versión Mejorada)
===========================================================================
CLI interactiva para soporte técnico usando Ansible como motor de ejecución.

Características mejoradas:
- Menú interactivo con Questionary (selección por números/letras y flechas)
- UI moderna mejorada con Rich (dashboard style)
- Ejecución de playbooks Ansible con JSON output
- Ejecución en segundo plano para tareas read-only
- Abrir consola remota en nueva ventana/terminal
- Health check antes de mostrar menú
- Validación de seguridad para target_host
- Dashboard de tareas en tiempo real
- Historial de sesión

Uso:
    python app.py

Estructura del código:
    cli/
    ├── config.py         # Configuración global (paths, logging, console)
    ├── models.py         # Dataclasses (MenuOption, MenuCategory, ExecutionResult)
    ├── menu_data.py      # Definición del menú completo
    ├── ansible_runner.py # Funciones de ejecución de Ansible (mejorado)
    ├── display.py        # Funciones de visualización con Rich (mejorado)
    ├── prompts.py        # Funciones de entrada de usuario
    ├── menus.py          # Funciones de navegación de menú (mejorado)
    └── history.py        # Sistema de historial de sesión
"""

import questionary

from cli import (
    console,
    check_environment,
    clear_screen,
    show_banner,
    show_menu_summary,
    solicitar_vault_password,
    mostrar_menu_categorias,
    mostrar_menu_opciones,
    ejecutar_opcion,
    CUSTOM_STYLE,
)
from cli.task_panel import get_task_panel
from rich.panel import Panel
from rich import box
from rich.layout import Layout
import questionary


def create_layout() -> Layout:
    """
    Crea el layout principal con panel lateral.
    
    Returns:
        Layout: Layout de Rich con header, main y footer
    """
    layout = Layout()
    
    # Header: Banner
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=1)
    )
    
    # Main: Dividir en menú (izquierda) y panel (derecha)
    layout["main"].split_row(
        Layout(name="menu", ratio=7),
        Layout(name="panel", ratio=3, visible=False)
    )
    
    return layout


def render_main_layout(layout: Layout, show_panel: bool = False) -> None:
    """
    Renderiza el layout principal con el contenido actual.
    
    Args:
        layout: Layout de Rich
        show_panel: Si mostrar el panel lateral
    """
    # Header: Banner
    banner_text = """IT-OPS CLI
🚀 Automatización IT con Ansible - Dashboard Pro
v2.0 - Mejorado"""
    width = console.width if hasattr(console, 'width') else 80
    lines = banner_text.split('\n')
    centered_lines = []
    for line in lines:
        padding = (width - len(line.strip())) // 2
        centered_lines.append(' ' * max(0, padding) + line.strip())
    banner = '\n'.join(centered_lines)
    layout["header"].update(Panel(banner, border_style="cyan", box=box.ROUNDED))
    
    # Footer: Atajos
    footer_text = "[dim][T] Toggle Panel | [D] Dashboard | [H] Historial | [X] Salir[/dim]"
    layout["footer"].update(footer_text)
    
    # Panel: Tareas activas (solo si hay tareas o está habilitado)
    if show_panel:
        layout["panel"].visible = True
        task_panel = get_task_panel()
        layout["panel"].update(task_panel)
    else:
        layout["panel"].visible = False


def main():
    """
    Función principal de la aplicación mejorada.
    
    Flujo:
    1. Mostrar banner mejorado
    2. Solicitar vault password (opcional)
    3. Loop de menú mejorado (sin pedir hostname inicial)
    4. Panel lateral de seguimiento de tareas
    """
    try:
        check_environment()
        
        # Solicitar vault password (opcional) una sola vez
        vault_password = solicitar_vault_password()
        
        # Crear layout principal
        layout = create_layout()
        show_panel = False
        
        # Loop principal
        while True:
            clear_screen()
            
            # Renderizar layout
            render_main_layout(layout, show_panel)
            
            # Imprimir layout directamente
            console.print(layout)
            
            # Mostrar resumen del menú (si no hay panel)
            if not show_panel:
                show_menu_summary()
            
            # Seleccionar categoría (con selección por números/letras)
            categoria = mostrar_menu_categorias()
            
            if categoria is None:
                # Salir
                break
            
            # Acciones especiales
            if categoria.key == "T":
                # Toggle panel
                show_panel = not show_panel
                continue
            elif categoria.key == "D":
                # Dashboard completo
                from cli.task_manager import task_manager
                all_tasks = task_manager.get_all_tasks()
                if all_tasks:
                    from cli.display import mostrar_historial_sesion
                    from cli.history import ExecutionStats
                    # Convertir a ExecutionStats para mostrar
                    stats = []
                    for task in all_tasks:
                        if task.result:
                            stats.append(ExecutionStats(
                                timestamp=task.start_time.strftime("%H:%M:%S") if task.start_time else "-",
                                hostname=task.target,
                                task_name=task.task_name,
                                success=task.status == "SUCCESS",
                                duration=task.duration,
                                job_id=task.task_id
                            ))
                    mostrar_historial_sesion(stats)
                    questionary.press_any_key_to_continue("Presione cualquier tecla para continuar...").ask()
                else:
                    console.print("[yellow]No hay tareas registradas[/yellow]")
                    questionary.press_any_key_to_continue("Presione cualquier tecla para continuar...").ask()
                continue
            elif categoria.key == "H":
                # Historial
                from cli.display import mostrar_historial_sesion
                from cli.history import session_history
                mostrar_historial_sesion(session_history.get_entries())
                questionary.press_any_key_to_continue("Presione cualquier tecla para continuar...").ask()
                continue
            elif categoria.key == "0":
                # Cambiar equipo (ya no se usa, pero mantenemos para compatibilidad)
                continue
            
            # Seleccionar opción (con selección por números/letras)
            opcion = mostrar_menu_opciones(categoria)
            
            if opcion is None:
                # Volver al menú de categorías
                continue
            
            # Ejecutar opción (con soporte para segundo plano y nueva ventana)
            # Ya no pasamos hostname - la función lo solicita si es necesario
            ejecutar_opcion(opcion, hostname=None, vault_password=vault_password)
            
            # Si se lanzaron tareas en background, mostrar panel automáticamente
            from cli.task_manager import task_manager
            if task_manager.get_active_tasks():
                show_panel = True
        
        console.print("\n[green]¡Gracias por usar IT-Ops CLI![/green]\n")
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Programa interrumpido por el usuario[/yellow]\n")
    except Exception as e:
        console.print(Panel(
            f"[red]Error inesperado: {e}[/red]",
            title="Error",
            border_style="red",
            box=box.ROUNDED
        ))
        raise


if __name__ == "__main__":
    main()
