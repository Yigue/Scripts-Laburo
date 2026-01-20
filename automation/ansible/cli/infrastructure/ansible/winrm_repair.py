# -*- coding: utf-8 -*-
"""
infrastructure/ansible/winrm_repair.py
=====================================
Utilidades para reparar WinRM.

Muestra comandos de PowerShell para reparar WinRM localmente.
"""

from rich.panel import Panel

from ...shared.config import console


def repair_winrm_local():
    """
    Muestra los comandos para reparar WinRM en la máquina local.
    """
    repair_cmds = [
        "Enable-PSRemoting -Force",
        "Set-NetConnectionProfile -NetworkCategory Private",
        "winrm quickconfig -q",
        "winrm set winrm/config/service '@{AllowUnencrypted=\"true\"}'",
        "winrm set winrm/config/service/auth '@{Basic=\"true\"}'",
        "New-NetFirewallRule -DisplayName \"WSL to WinRM\" -Direction Inbound -LocalPort 5985 -Protocol TCP -Action Allow -RemoteAddress 172.27.144.0/24"
    ]
    
    console.print(Panel(
        "\n".join([f"[bold cyan]{c}[/bold cyan]" for c in repair_cmds]),
        title="🛠️ Reparación de WinRM (PowerShell Admin)",
        border_style="yellow"
    ))
    console.print("\n[yellow]Copia y pega estos comandos en una consola de PowerShell con privilegios de Administrador.[/yellow]\n")
