# IT-Ops CLI PRO - Background Execution System

Sistema de ejecución asíncrona para playbooks de Ansible con interfaz interactiva y dashboard en tiempo real.

## Características

1. **Modelo No Bloqueante**: Lanzá playbooks y seguí trabajando sin esperar a que terminen
2. **Dashboard en Tiempo Real**: Monitoreá todas las tareas activas en un panel visual
3. **Menú Interactivo**: Interfaz clara con categorías organizadas
4. **Ejecución Asíncrona**: Múltiples tareas ejecutándose en paralelo

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

### Menú Interactivo (Recomendado)
```bash
python app.py
# o específicamente:
python app.py menu
```

### Solo Dashboard
```bash
python app.py dashboard
```

## Estructura del Proyecto

```
testSecondplaner/
├── app.py                 # Punto de entrada principal
├── core/
│   └── engine.py         # Motor de ejecución asíncrona
├── ui/
│   ├── dashboard.py      # Dashboard en tiempo real
│   └── menu.py           # Menú interactivo
├── config/
│   └── menu_data.py      # Configuración de menús y playbooks
├── requirements.txt       # Dependencias Python
└── README.md             # Esta documentación
```

## Componentes

- **BackgroundEngine**: Gestiona jobs y ejecución en hilos separados
- **Dashboard**: Visualización en tiempo real de jobs activos y logs
- **MainMenu**: Menú interactivo para lanzar tareas y gestionar targets

## Modos de Ejecución

1. **Menú Interactivo**: Navegá por categorías y lanzá tareas fácilmente
2. **Dashboard**: Monitoreá tareas activas con logs en tiempo real
