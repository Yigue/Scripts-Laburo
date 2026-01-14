# IT-Ops CLI PRO (Versión Mejorada)

Esta carpeta contiene la propuesta de mejora de UI/UX para el IT-Ops CLI, integrando el sistema de ejecución asíncrona.

## Cambios Clave de Diseño (UX)

1.  **Modelo No Bloqueante**: En la versión original (`app.py`), cuando lanzás un playbook, tenés que esperar a que termine para hacer cualquier otra cosa. En **`app_professional.py`**, las tareas se envían al motor de segundo plano y podés seguir navegando por los menús inmediatamente.
2.  **Visibilidad de Estado**: La cabecera muestra siempre el equipo seleccionado y cuántos trabajos están corriendo actualmente.
3.  **Monitoreo Centralizado**: En lugar de ver los logs pasar rápido por la pantalla, tenés un **Dashboard** dedicado donde podés monitorear todas las tareas juntas, ver cuáles fallaron y cuáles terminaron, con sus respectivos logs secundarios.
4.  **Consistencia Visual**: Uso de Layouts de Rich para una interfaz que se siente como una aplicación moderna y no solo un script de consola.

## Cómo ejecutar

Desde la raíz del proyecto o dentro de esta carpeta:
```bash
python testSecondplaner/app_professional.py
```

## Estructura de Archivos
- `engine.py`: Motor de gestión de hilos y procesos.
- `dashboard.py`: Interfaz visual dinámica.
- `app_professional.py`: El punto de entrada que combina el menú interactivo con el motor asíncrono.
