#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IT-Ops CLI - Herramienta de Automatización con Ansible
"""

import questionary

from cli import (
    console,
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
            if categoria.key == "HI":
                from cli.display import mostrar_historial_sesion
                from cli.history import get_entries as history_get_entries
                mostrar_historial_sesion(history_get_entries())
                questionary.press_any_key_to_continue("Presione cualquier tecla para continuar...").ask()
                continue
            elif categoria.key == "D":
                from cli.task_manager import get_all_tasks as task_get_all_tasks
                all_tasks = task_get_all_tasks()
                if all_tasks:
                    from cli.display import mostrar_historial_sesion
                    from cli.models import ExecutionStats
                    stats = []
                    for task in all_tasks:
                        if task.result:
                            stats.append(ExecutionStats(
                                timestamp=task.start_time.strftime("%H:%M:%S") if task.start_time else "-",
                                hostname=task.target,
                                task_name=task.task_name,
                                success=task.status == "SUCCESS",
                                duration=task.duration
                            ))
                    mostrar_historial_sesion(stats)
                    questionary.press_any_key_to_continue("Presione cualquier tecla para continuar...").ask()
                else:
                    console.print("[yellow]No hay tareas registradas[/yellow]")
                    questionary.press_any_key_to_continue("Presione cualquier tecla para continuar...").ask()
                continue
            elif categoria.key == "0":
                continue
            
            # Seleccionar opción
            #region agent log
            import json
            log_path = "/home/korg/Scripts-Laburo/automation/ansible/.cursor/debug.log"
            try:
                with open(log_path, "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "app.py:73", "message": "Antes de mostrar_menu_opciones", "data": {"categoria_key": categoria.key, "categoria_name": categoria.name}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
            #endregion
            opcion = mostrar_menu_opciones(categoria)
            #region agent log
            try:
                with open(log_path, "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "app.py:74", "message": "Después de mostrar_menu_opciones", "data": {"opcion": opcion.key if opcion else None, "opcion_label": opcion.label if opcion else None, "is_none": opcion is None}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
            #endregion
            
            if opcion is None:
                #region agent log
                try:
                    with open(log_path, "a") as f:
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "app.py:77", "message": "Opción es None, saltando", "data": {}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
                except: pass
                #endregion
                continue
            
            # Ejecutar opción
            #region agent log
            try:
                with open(log_path, "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "app.py:79", "message": "Antes de ejecutar_opcion", "data": {"opcion_key": opcion.key, "opcion_label": opcion.label, "has_vault": vault_password is not None}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except: pass
            #endregion
            try:
                ejecutar_opcion(opcion, hostname=None, vault_password=vault_password)
                #region agent log
                try:
                    with open(log_path, "a") as f:
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "app.py:85", "message": "Después de ejecutar_opcion (exitoso)", "data": {}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
                except: pass
                #endregion
            except Exception as e:
                #region agent log
                try:
                    with open(log_path, "a") as f:
                        f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "B", "location": "app.py:87", "message": "Error en ejecutar_opcion", "data": {"error_type": type(e).__name__, "error_msg": str(e)}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
                except: pass
                #endregion
                raise
        
        console.print("\n[green]¡Gracias por usar IT-Ops CLI![/green]\n")
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Programa interrumpido por el usuario[/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        raise


if __name__ == "__main__":
    main()
