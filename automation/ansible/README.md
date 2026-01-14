# IT-Ops CLI (Automation Hub)

## Principios de Diseño y Filosofía

Este proyecto combina la potencia de **Ansible** con la versatilidad de **Python** para crear una herramienta de automatización robusta y escalable.

- **Enfoque "Read-only First"**: Priorizar operaciones de **lectura, auditoría y obtención de información** antes que acciones destructivas.
- **Standards**: Priorizar el uso de **colecciones oficiales y community** de Ansible antes que recurrir a `win_shell` o `win_command`.
- **Arquitectura Híbrida**:
    - **Ansible**: Orquestador y motor declarativo.
    - **Python**: Lógica compleja, parsing, correlación de datos, generación de reportes e interfaz de usuario (CLI/TUI).
- **Seguridad y Estabilidad**:
    - Scripts diseñados para ser **idempotentes**.
    - Ejecutables en modo `check` (dry-run).
    - Claramente separados en Consultas, Acciones, y Remediaciones.

---

## Collection y librerias que voy a usar

### Python (Orquestación e Interfaz)

- **`ansible-runner`**: Librería oficial para ejecutar Playbooks desde Python de forma programática. Permite capturar eventos, logs y output JSON de forma nativa.
- **`pywinrm[ntlm]`**: Indispensable para establecer la conexión remota con Windows utilizando autenticación NTLM (según requerimientos de seguridad corporativa).
- **`rich`**: Para renderizar tablas, barras de progreso, paneles y colores en la terminal (TUI), mejorando la experiencia de usuario.
- **`questionary`**: Para la creación de menús interactivos, selectores y confirmaciones de seguridad antes de ejecutar acciones críticas.
- **`pandas`**: (Roadmap) Para procesar datos de inventarios complejos y exportar reportes (CSV/Excel) solicitados en la sección de AD y Hardware.

### Ansible (Motor de Automatización)

- **`ansible.windows`**: Colección core. Manejo de archivos, servicios, usuarios locales y reinicios.
- **`community.windows`**: **Crítica para tu roadmap.**
    - Interactúa con **WMI/CIM** (necesario para invocar ciclos de **SCCM**).
    - Gestión avanzada de actualizaciones (Windows Update).
    - Manejo de tareas programadas y registro (Regedit).
- **`microsoft.ad`**: Estándar moderno para interactuar con Active Directory. Permite consultas complejas, manejo de grupos y recuperación segura de **LAPS** y **BitLocker**.
- **`cisco.ios` / `ansible.netcommon`**: Para la conexión vía **SSH** a la **WLC** (Wireless LAN Controller) y ejecución de comandos `show` para el diagnóstico de red.
- **`community.general`**: Utilidades varias, manejo de archivos CSV, lógica de control y notificaciones.

### Otros (Sistema Base)

- **`openssh-client`**: Necesario en el host local (WSL/Linux) para permitir que Ansible se conecte a la infraestructura de red (WLC/Switches).
- **`sshpass`**: Para manejo de autenticación SSH no interactiva si no se usan llaves RSA

## Secciones y Tareas

A continuación se detalla la cobertura actual del proyecto y las funcionalidades planificadas.

### 🔐 AD (Active Directory y Seguridad)

*Objetivo: Gestión de identidades, auditoría de objetos y recuperación de credenciales privilegiadas.*

**✅ Implementado:**

- **Desbloquear usuario de red**: `playbooks/admin/unlock_user.yml`
    - Desbloquea cuentas de dominio.
- **Obtener password Admin Local (LAPS)**: `playbooks/admin/get_laps_password.yml`
    - Recupera la contraseña de administrador local actual desde AD.
- **Ver clave BitLocker Recovery**: `playbooks/admin/get_bitlocker_key.yml`
    - Obtiene claves de recuperación de BitLocker almacenadas en AD.

**🚀 Planificado / Roadmap:**

- Listar usuarios de Active Directory con filtros (OU, estado, fecha de último logon).
- Obtener membresías de grupos críticos (Admins, grupos de aplicaciones).
- Listar equipos del dominio con SO, último logon y estado de cuenta.
- Auditoría de usuarios y equipos inactivos.
- Validación de atributos clave (mail, department, description).
- Exportación de información a JSON / CSV para reporting.

---

### 📡 SCCM Co (Endpoint Management)

*Objetivo: Integración con MECM/SCCM para inventario y gestión de agentes, usándolo como fuente complementaria.*

**✅ Implementado:**

- *(Integración parcial vía drivers y actualizaciones en Hardware)*

**🚀 Planificado / Roadmap:**

- Listar dispositivos registrados en SCCM / MECM.
- consultar  informacion de 1 eqipo de SCCM
- Consultar estado de cliente SCCM en equipos (activo, inactivo, errores).
- Obtener colecciones a las que pertenece un equipo.
- Auditoría de equipos sin cliente o que no reportan.
- Disparar acciones **no invasivas** (Machine Policy Retrieval, Software Inventory Cycle).
- Relizar acciones, gpupdate , politicas
- Acciones para forzar actualziacion del ultimo equipo

---

### 📶 WIFI (Infraestructura Wireless)

*Objetivo: Auditoría de estado, diagnóstico de conexión y validación de cobertura.*

**✅ Implementado:**

- **Analizador Wi-Fi**: `playbooks/network/wifi_analyzer.yml`
    - Diagnóstico de señal (RSSI), BSSID y canal del cliente actual.
- **WCORP Fix**: `playbooks/network/wcorp_fix.yml`
    - Remediación automática de problemas de conexión corporativa.
- **Reparar red**: `playbooks/network/network_repair.yml` (Nivel cliente).
- **Test de Velocidad**: `playbooks/network/speedtest.yml`.
- **Ancho de banda**: `playbooks/network/bandwidth_usage.yml`.

**🚀 Planificado / Roadmap:**

- Restablecer adaptador de reds

---

### 📦 Windows y Aplicaciones

*Objetivo: Gestión del ciclo de vida del software, inventario y configuración del sistema operativo.*

**✅ Implementado:**

- **Listar/Desinstalar aplicaciones**: `playbooks/software/manage_apps.yml`
    - Inventario de software y desinstalación interactiva.
- **Instalar Office 365**: `playbooks/software/install_office.yml`
    - Instalación silenciosa de la suite.
- **Reparar Office**: `playbooks/software/repair_office.yml`
    - Ejecución de Quick Repair.
- **Resetear OneDrive**: `playbooks/software/reset_onedrive.yml`.
- **Activar Windows**: `playbooks/hardware/activate_windows.yml`.

**🚀 Planificado / Roadmap:**

- Listar aplicaciones diferenciando MSI de no-MSI. on diferente information
- Identificar aplicaciones fuera de estándar ("Shadow IT").
- instalacion aplicaciones  que busque instaladores en la pc de soporte y dsp las intale
- Gestión de servicios Windows (estado, tipo de inicio).
- Validación de features y roles de Windows.
- Handlers para reinicios controlados de servicios o SO.

---

### 💻 Hardware y Diagnóstico

*Objetivo: Telemetría de hardware, salud de componentes y mantenimiento preventivo.*

**✅ Implementado:**

- **Mostrar especificaciones**: `playbooks/hardware/specs.yml`
    - CPU, RAM, Disco, Serial.
- **Salud de Batería**: `playbooks/hardware/battery_health.yml`.
- **Reporte SMART de Disco**: `playbooks/hardware/disk_smart.yml`.
- **Actualizar drivers DELL**: `playbooks/hardware/dell_drivers.yml` (Dell Command | Update).
- **Optimizar sistema**: `playbooks/hardware/optimize.yml`.
- **Reiniciar equipo**: `playbooks/hardware/reboot.yml`.

**🚀 Planificado / Roadmap:**

- Testeode  performance
- Recolección de logs básicos para diagnóstico remoto.
- Limpieza de cache y archivos basuras
- limpieza de usuarios viejos
- Inventario general unificado (AD + SCCM + Windows + Red).

---

### 🌐 Conexión y Consultas WLC

*Objetivo: Gestión de controladores inalámbricos (Wireless LAN Controllers) vía SSH/CLI.*

**✅ Implementado:**

**🚀 Planificado / Roadmap:**

- Conexión vía SSH a WLC.
- Ejecución de comandos `show` para estado de controladoras y APs.
- Ver Todos los aps y breve informacion de cada uno solo los aps de CIT
- ver todos los clientes conectados a 1 ap
- ver toda la información de un cliente por ip /hostname
- realizar búsqueda de ip, hostname y todo
- generar reporte para telecomunicaciones

---

### 🔍 Monitoreo (futura implementacion primero todo lo primero

*Objetivo: Supervisión continua y health-checks.*

**✅ Implementado:**

- **Health Check WinRM**: Integrado en `app.py` (check_online), verifica disponibilidad antes de ejecutar.
- **Logs de Ejecución**: Almacenados localmente.

**🚀 Planificado / Roadmap:**

- Chequeos periódicos de estado (Infra, Windows, Red).
- Recolección de métricas clave y salida estructurada (JSON).
- Integración con dashboards o sistemas de alertas externos.

---

### 💻 Impresora

*Objetivo: Telemetría de hardware, salud de componentes y mantenimiento preventivo.*

**✅ Implementado:**

- **Gestionar impresoras**: `playbooks/printers/manage_printers.yml`.
- **Calibrar Zebra**: `playbooks/printers/zebra_calibrate.yml`.

**🚀 Planificado / Roadmap:**

- Testeode  performance

### 🛠️ Otras Categorías (Impresoras / Utilidades)

**✅ Implementado:**

- **Consola Remota**: `playbooks/remote/console.yml`.

**🚀 Planificado / Roadmap:**

- 

---

## Estructura Definida en el Proyecto

La arquitectura del proyecto sigue estrictas normas de separación de responsabilidades para garantizar mantenibilidad y escalabilidad.

### Organización de Archivos

```
it-ops-cli/
├── app.py                 # Orquestador UI (Python) - Menús y lógica de presentación
├── inventory/             # Definición de targets
│   ├── hosts.ini          # Inventario estático (Dev) o dinámico (AD)
│   └── group_vars/        # Variables por entorno (Dev/Prod)
├── playbooks/             # Lógica de Automatización (Ansible)
│   ├── admin/             # Tareas de AD y Seguridad
│   ├── hardware/          # Tareas de Hardware y Mantenimiento
│   ├── network/           # Consultas y arreglos de red
│   ├── software/          # Gestión de paquetería
│   └── ...
├── roles/                 # Código reutilizable y modular
│   ├── common/            # Configuraciones base
│   └── ...
└── logs/                  # Registro de auditoría

```

### Principios de Implementación

1. **Separación de Capas**:
    - **Inventario**: Define *dónde* se ejecuta.
    - **Identificación (Vars)**: Define *con qué datos* se ejecuta.
    - **Lógica (Playbooks/Roles)**: Define *qué* se ejecuta.
2. **Modularidad**:
    - Uso extensivo de **Roles** para encapsular lógica repetitiva.
    - Distinción clara entre playbooks de **Consulta** (solo lectura, rápidos) y **Acción/Remediación** (cambios de estado, requieren confirmación).
3. **Gestión de Entornos**:
    - Uso de `group_vars` y `host_vars` para manejar diferencias entre desarrollo, staging y producción sin tocar el código de los playbooks.
4. **Buenas Prácticas**:
    - **Naming Convention**: Nombres descriptivos y consistentes (snake_case).
    - **Pureza**: Evitar lógica compleja en YAML; delegar procesamiento de datos a filtros de Python o scripts auxiliares cuando la lógica condicional se vuelve inmanejable en Ansible.
    - **Documentación Viva**: Este README y los comentarios en código deben mantenerse actualizados.