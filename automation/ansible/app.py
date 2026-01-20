#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IT-Ops CLI - Herramienta de Automatización con Ansible
"""

import questionary

from cli import (
    console,
    logger,
    check_environment,
    clear_screen,
    show_banner,
    solicitar_vault_password,
    mostrar_menu_categorias,
    mostrar_menu_opciones,
    ejecutar_opcion,
)


def main():
    """
    Función principal - Diseño minimalista mejorado.
    """
    try:
        check_environment()
        vault_password = solicitar_vault_password()
        
        # Loop principal
        while True:
            clear_screen()
            show_banner()
            
            # Seleccionar categoría
            categoria = mostrar_menu_categorias()
            
            if categoria is None:
                break
            
            # Acciones especiales
            if not hasattr(categoria, 'key'):
                continue
            
            if categoria.key == "HI":
                from cli import mostrar_historial_sesion, history_get_entries
                try:
                    mostrar_historial_sesion(history_get_entries())
                except Exception as e:
                    console.print(f"[red]Error mostrando historial: {e}[/red]")
                    logger.error(f"Error mostrando historial: {e}", exc_info=True)
                questionary.press_any_key_to_continue("Presione cualquier tecla para continuar...").ask()
                continue
            elif categoria.key == "D":
                from cli import task_get_all_tasks, mostrar_historial_sesion, ExecutionStats
                try:
                    all_tasks = task_get_all_tasks()
                    if all_tasks:
                        stats = []
                        for task in all_tasks:
                            if task.result:
                                try:
                                    stats.append(ExecutionStats(
                                        timestamp=task.start_time.strftime("%H:%M:%S") if task.start_time else "-",
                                        hostname=task.target or "N/A",
                                        task_name=task.task_name or "N/A",
                                        success=task.status == "SUCCESS",
                                        duration=task.duration or 0
                                    ))
                                except Exception as e:
                                    logger.error(f"Error procesando tarea {task.task_id}: {e}", exc_info=True)
                                    continue
                        if stats:
                            mostrar_historial_sesion(stats)
                        else:
                            console.print("[yellow]No hay tareas con resultados disponibles[/yellow]")
                    else:
                        console.print("[yellow]No hay tareas registradas[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error mostrando dashboard: {e}[/red]")
                    logger.error(f"Error mostrando dashboard: {e}", exc_info=True)
                questionary.press_any_key_to_continue("Presione cualquier tecla para continuar...").ask()
                continue
            
            # Seleccionar opción
            try:
                from cli.infrastructure.logging.debug_logger import debug_logger
                debug_logger.log(
                    "app.py",
                    "Antes de mostrar_menu_opciones",
                    {"categoria_key": categoria.key, "categoria_name": getattr(categoria, 'name', 'N/A')},
                    hypothesis_id="A"
                )
            except ImportError:
                debug_logger = None
            
            try:
                opcion = mostrar_menu_opciones(categoria)
                if debug_logger:
                    debug_logger.log(
                        "app.py",
                        "Después de mostrar_menu_opciones",
                        {"opcion": opcion.key if opcion and hasattr(opcion, 'key') else None, 
                         "opcion_label": opcion.label if opcion and hasattr(opcion, 'label') else None, 
                         "is_none": opcion is None},
                        hypothesis_id="A"
                    )
            except Exception as e:
                console.print(f"[red]Error mostrando opciones: {e}[/red]")
                logger.error(f"Error mostrando opciones: {e}", exc_info=True)
                questionary.press_any_key_to_continue("Presione cualquier tecla para continuar...").ask()
                continue
            
            if opcion is None:
                if debug_logger:
                    debug_logger.log("app.py", "Opción es None, saltando", {}, hypothesis_id="A")
                continue
            
            # Ejecutar opción
            if debug_logger:
                debug_logger.log(
                    "app.py",
                    "Antes de ejecutar_opcion",
                    {"opcion_key": getattr(opcion, 'key', 'N/A'), 
                     "opcion_label": getattr(opcion, 'label', 'N/A'), 
                     "has_vault": vault_password is not None},
                    hypothesis_id="B"
                )
            try:
                ejecutar_opcion(opcion, hostname=None, vault_password=vault_password)
                if debug_logger:
                    debug_logger.log("app.py", "Después de ejecutar_opcion (exitoso)", {}, hypothesis_id="B")
            except KeyboardInterrupt:
                console.print("\n[yellow]Operación cancelada por el usuario[/yellow]\n")
                if debug_logger:
                    debug_logger.log("app.py", "Ejecución cancelada por usuario", {}, hypothesis_id="B")
            except Exception as e:
                if debug_logger:
                    debug_logger.log(
                        "app.py",
                        "Error en ejecutar_opcion",
                        {"error_type": type(e).__name__, "error_msg": str(e)},
                        hypothesis_id="B"
                    )
                console.print(f"\n[red]Error ejecutando opción: {e}[/red]\n")
                logger.error(f"Error ejecutando opción: {e}", exc_info=True)
                questionary.press_any_key_to_continue("Presione cualquier tecla para continuar...").ask()
        
        console.print("\n[green]¡Gracias por usar IT-Ops CLI![/green]\n")
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Programa interrumpido por el usuario[/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        raise


if __name__ == "__main__":
    main()
