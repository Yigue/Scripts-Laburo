🚀 Proyecto: IT-Ops CLI (Automation Hub)
1. Visión General
Una herramienta de línea de comandos (CLI) interactiva basada en Python y Ansible para centralizar tareas de soporte técnico de Nivel 1 y 2. Permite diagnosticar, reparar y configurar estaciones de trabajo Windows de forma remota, estandarizada y escalable.

Diferencia clave con tu script anterior:

Antes: El script ejecutaba comandos directos. Si fallaba a la mitad, no sabías qué pasó.

Ahora: Python dibuja el menú, pero le pide a Ansible que ejecute la tarea. Ansible garantiza que si le dices "Instalar Chrome", verifique si ya está instalado antes de intentar instalarlo de nuevo (Idempotencia).

2. Arquitectura Técnica
Stack Tecnológico
Controlador (Tu máquina): Python 3.10+ + Ansible Core.

Interfaz (TUI): Librería questionary o textual (Python) para menús modernos y navegables con teclado.

Motor de Ejecución: Ansible Playbooks (YAML).

Conexión: WinRM (Kerberos en Prod / Basic en Dev).

Objetivos: Windows 10/11 Enterprise.

Estructura de Carpetas Recomendada
Esta estructura es profesional y escalable.

Plaintext

it-ops-cli/
├── app.py                 # Tu menú principal en Python (el "frontend")
├── inventory/
│   ├── hosts.ini          # Inventario (Dev/Prod)
│   └── group_vars/        # Variables (credenciales, paths de software)
├── playbooks/             # Aquí vive la lógica de Ansible
│   ├── hardware/
│   │   ├── specs.yml
│   │   └── drivers_dell.yml
│   ├── network/
│   │   ├── wcorp_fix.yml
│   │   └── wifi_info.yml
│   ├── software/
│   │   ├── install_list.yml
│   │   └── uninstall.yml
│   └── printers/
│       └── zebra_calib.yml
├── scripts/               # Scripts complejos de PowerShell (auxiliares)
│   └── get_ap_info.ps1
└── requirements.txt       # Dependencias de Python
3. Propuesta de Funcionalidades (Mejoradas)
Basado en tu lista, he añadido funcionalidades "Pro" que aprovechan Ansible y que son vitales en entornos corporativos.

🌐 [R] Redes y Conectividad
Tu idea: Arreglos WCORP, Escaneo, Ver AP.

Upgrade:

Diagnóstico de Velocidad (iperf/speedtest): Ejecutar un test de velocidad CLI remoto para ver si el usuario realmente tiene internet lento.

Info detallada del AP (BSSID/Signal): Usar netsh wlan show interfaces y parsear la salida para ver la calidad de la señal en % real.

Flush DNS & Reset IP: No solo un script, sino reiniciar la interfaz de red limpiamente.

💻 [H] Hardware y Sistema
Tu idea: Specs, Config, Optimización, Drivers Dell.

Upgrade:

Salud del Disco (SMART): Verificar si el disco sólido está por morir antes de optimizar.

Windows Updates Check: Listar qué actualizaciones de seguridad le faltan.

Estado de BitLocker: Ver si el disco está encriptado y si la clave está backupeada en AD.

📦 [S] Software
Tu idea: Instalar/Desinstalar.

Upgrade:

Catálogo de Software: En lugar de "Instalar X", tener un archivo YAML con una lista (Chrome, 7Zip, Adobe, SAP) y poder seleccionar varios con barra espaciadora para instalar en lote.

Reparar Office: Ejecutar el "Quick Repair" de Office de forma remota.

🖨️ [I] Impresoras
Tu idea: Spooler, Zebra ZPL.

Upgrade:

Mapeo de Impresoras por GPO: Forzar un gpupdate /force específico para políticas de usuario (impresoras).

Limpieza de Cola: Borrar trabajos atascados antes de reiniciar el spooler.

Envío de ZPL Raw: Enviar código ZPL directamente al puerto 9100 de la Zebra para calibrar sin driver.

🔧 [A] Admin & AD (Nuevo)
Upgrade:

Desbloquear Cuenta: Buscar el usuario logueado en esa PC y desbloquearlo en AD.

LAPS: Leer la contraseña de administrador local (si usan LAPS).

Ultimo Reboot: Saber hace cuánto no reinicia el usuario (clave para solucionar problemas fantasmas).

4. Documentación Técnica del Proyecto
Este sería el README.md que vería tu jefe o tus compañeros.

Título: IT-Operations Automation CLI
Descripción: Herramienta de orquestación para soporte técnico distribuido. Permite la ejecución remota de tareas de mantenimiento, instalación y diagnóstico sobre infraestructura Windows utilizando Ansible como motor de configuración.

Prerrequisitos:

Acceso de red al puerto 5985 (HTTP) o 5986 (HTTPS) de los clientes.

Cuenta de servicio con permisos de Administrador Local en los equipos target.

Módulos Principales:

1. Módulo de Sistema (playbooks/system/)
Utiliza ansible.windows.win_shell y win_service.

Get-Specs: Recopila facts (ansible_facts) y consultas WMI para obtener Serial, Modelo, RAM y Usuario actual.

Dell-Update: Invoca dcu-cli.exe (Dell Command Update) para buscar drivers críticos de BIOS/Firmware.

2. Módulo de Red (playbooks/network/)
Wifi-Analyzer: Ejecuta scripts remotos de PowerShell para extraer BSSID del Access Point y fuerza de señal (RSSI).

Net-Repair: Ejecuta una secuencia de: ipconfig /flushdns, nbtstat -R, y reinicio de adaptador Wi-Fi.

3. Módulo de Software (playbooks/software/)
Utiliza ansible.windows.win_package.

Gestiona instalaciones silenciosas (/S, /qn) ubicadas en repositorios de red (SMB Shares).

Permite desinstalación por ID de producto (GUID).

4. Módulo de Impresoras (Zebra/Spooler)
Zebra-Calib: Envía cadenas hexadecimales ZPL (~JC, ~JG) directamente al puerto de comunicación para calibración de medios sin intervención del usuario.

5. Plan de Acción (Tu Roadmap)
Como estás probando en local ahora, vamos paso a paso:

Fase 1: El Core (Esta semana)
Montar la estructura de carpetas que te puse arriba.

Crear el menú en Python: No uses simples print, usa la librería questionary (es fácil, pip install questionary). Te permite seleccionar con flechitas.

Conectar Python con Ansible: Tu script de Python simplemente construirá el comando ansible-playbook ... y lo ejecutará con subprocess.run().

Fase 2: Migrar Funciones (Tu lista actual)
Crear el playbook wifi_info.yml (el que escanea AP).

Crear el playbook specs.yml (el de hardware).

Probarlos contra tu máquina local y tu VM.

Fase 3: Escalabilidad (Cuando pases a Prod)
Configurar Kerberos en tu Linux/WSL.

Cambiar el archivo hosts.ini para que apunte a las IPs de la empresa.