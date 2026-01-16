#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IT-Ops CLI - Herramienta de Automatización con Ansible
======================================================
CLI interactiva para soporte técnico usando Ansible como motor de ejecución.

Características:
- Menú interactivo con Questionary
- UI moderna con Rich
- Ejecución de playbooks Ansible con JSON output
- Health check antes de mostrar menú
- Validación de seguridad para target_host
- Integración con Active Directory (LAPS, BitLocker, Unlock)

Uso:
    python app.py

Estructura del código:
    cli/
    ├── config.py         # Configuración global (paths, logging, console)
    ├── models.py         # Dataclasses (MenuOption, MenuCategory, ExecutionResult)
    ├── menu_data.py      # Definición del menú completo
    ├── ansible_runner.py # Funciones de ejecución de Ansible
    ├── display.py        # Funciones de visualización con Rich
    ├── prompts.py        # Funciones de entrada de usuario
    └── menus.py          # Funciones de navegación de menú
"""

import questionary

from cli import (
    console,
    check_environment,
    check_online,
    clear_screen,
    show_banner,
    show_menu_summary,
    solicitar_hostname,
    solicitar_vault_password,
    mostrar_menu_categorias,
    mostrar_menu_opciones,
    ejecutar_opcion,
    obtener_host_snapshot,
    mostrar_host_snapshot,
    CUSTOM_STYLE,
)
from rich.panel import Panel


def main():
    """
    Función principal de la aplicación.
    
    Flujo:
    1. Mostrar banner
    2. Solicitar vault password (opcional)
    3. Solicitar hostname
    4. Health check
    5. Loop de menú
    """
    try:
        check_environment()
        clear_screen()
        show_banner()
        
        # Mostrar resumen del menú
        show_menu_summary()
        
        # Solicitar vault password (opcional)
        vault_password = solicitar_vault_password()
        
        while True:
            # Solicitar hostname
            hostname = solicitar_hostname()
            if hostname is None:
                console.print("\n[yellow]Saliendo...[/yellow]")
                break
            
            # Health check
            if not check_online(hostname, vault_password):
                if not questionary.confirm(
                    "¿Intentar con otro hostname?",
                    style=CUSTOM_STYLE,
                    default=True
                ).ask():
                    break
                continue
            
            # Obtener Snapshot inicial
            snapshot = obtener_host_snapshot(hostname, vault_password)
            
            # Loop del menú
            while True:
                clear_screen()
                show_banner()
                
                if snapshot:
                    mostrar_host_snapshot(snapshot)
                else:
                    console.print(f"[cyan]Host activo:[/cyan] [bold green]{hostname}[/bold green]\n")
                
                # Seleccionar categoría
                categoria = mostrar_menu_categorias()
                
                if categoria is None:
                    # Salir
                    break
                
                if categoria.key == "0":
                    # Cambiar equipo
                    break
                
                # Seleccionar opción
                opcion = mostrar_menu_opciones(categoria)
                
                if opcion is None:
                    # Volver al menú de categorías
                    continue
                
                # Ejecutar opción
                ejecutar_opcion(opcion, hostname, vault_password)
            
            # Preguntar si continuar con otro equipo
            if categoria is not None and categoria.key == "0":
                continue  # Cambiar equipo
            
            # Salir del programa
            break
        
        console.print("\n[green]¡Gracias por usar IT-Ops CLI![/green]\n")
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Programa interrumpido por el usuario[/yellow]\n")
    except Exception as e:
        console.print(Panel(
            f"[red]Error inesperado: {e}[/red]",
            title="Error",
            border_style="red"
        ))
        raise


if __name__ == "__main__":
    main()
