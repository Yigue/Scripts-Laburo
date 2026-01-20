# 📦 Guía Completa: Crear Ejecutable .exe para Windows

## Resumen

Esta guía explica cómo compilar la aplicación IT-Ops CLI en un ejecutable .exe para Windows, protegiendo el código fuente y facilitando la distribución.

## ✅ Solución Implementada: PyInstaller

Se ha configurado **PyInstaller** que es la herramienta más popular y confiable para crear ejecutables de Python.

### Archivos Creados:

1. **`build_exe.py`** - Script automatizado para construir el .exe
2. **`IT-Ops-CLI.spec`** - Archivo de especificación de PyInstaller
3. **Modificaciones en `config.py`** - Soporte para ejecución desde .exe

## 🚀 Proceso Paso a Paso

### Paso 1: Instalar PyInstaller

```bash
pip install pyinstaller
```

### Paso 2: Construir el Ejecutable

```bash
python build_exe.py
```

Esto generará el archivo `dist/IT-Ops-CLI.exe`

### Paso 3: Probar el Ejecutable

```bash
dist/IT-Ops-CLI.exe
```

## 📋 Qué Incluye el Ejecutable

El .exe incluye automáticamente:
- ✅ Todo el código Python compilado (protegido como bytecode)
- ✅ `inventory/` (incluyendo group_vars, pero ver advertencia de seguridad)
- ✅ `playbooks/`
- ✅ `roles/`
- ✅ `ansible.cfg`
- ✅ Todas las dependencias Python (questionary, rich, yaml, etc.)

## ⚠️ Consideraciones Importantes

### 1. Ansible NO se Incluye

El ejecutable **NO incluye Ansible**. El usuario destino debe tener:
- Ansible instalado
- En PATH del sistema

**Alternativas:**
- Incluir instalador de Ansible junto con el .exe
- Crear un instalador completo (Inno Setup, NSIS, WiX)

### 2. Seguridad del Vault

El archivo `inventory/group_vars/all/vault.yml` **se incluirá** en el .exe si existe.

**Recomendaciones:**
- ✅ NO incluir vault.yml en el repositorio (ya está en .gitignore)
- ✅ Usar variables de entorno para secretos en producción
- ✅ El usuario debe proporcionar su propio vault.yml externamente
- ✅ O modificar `build_exe.py` para excluirlo explícitamente

### 3. Tamaño del Ejecutable

El .exe resultante será aproximadamente:
- **50-100 MB** (incluye Python runtime + dependencias)
- Es normal y aceptable para aplicaciones Python

### 4. Requisitos del Sistema Destino

- Windows 10/11
- Ansible instalado
- PowerShell 5.1+
- WinRM habilitado (para conexiones remotas)

## 🔒 Protección del Código

### Lo que SÍ protege PyInstaller:
- ✅ Código Python compilado a bytecode (.pyc)
- ✅ No es fácilmente legible sin herramientas especializadas
- ✅ Reduce significativamente la exposición del código fuente

### Lo que NO protege completamente:
- ⚠️ Python bytecode puede ser decompilado con herramientas
- ⚠️ Para protección real necesitas obfuscación adicional

### Opciones para Mayor Protección:

1. **PyArmor** (Obfuscación):
   ```bash
   pip install pyarmor
   pyarmor gen --onefile app.py
   ```

2. **Nuitka** (Compilación a C++):
   ```bash
   pip install nuitka
   python -m nuitka --onefile app.py
   ```

3. **Licencias comerciales**: Usar herramientas comerciales de protección

## 🎯 Opciones de Configuración

### Ocultar Consola (Producción)

En `build_exe.py`, descomentar:
```python
'--windowed',  # Sin consola
```

**Ventaja**: Interfaz más profesional
**Desventaja**: No se ven logs de error si falla

### Mostrar Consola (Debugging) ⭐ Recomendado

Mantener comentado `--windowed` (por defecto muestra consola).

**Ventaja**: Puedes ver errores y logs
**Desventaja**: Se ve la consola de Windows

### Un Solo Archivo vs Directorio

- **`--onefile`** (recomendado): Un solo .exe (~50-100 MB)
- **`--onedir`**: Carpeta con varios archivos (~30-50 MB total)

## 📦 Distribución

### Opción 1: Solo el .exe

Distribuir:
- `dist/IT-Ops-CLI.exe`

El usuario debe tener Ansible instalado.

### Opción 2: Instalador Completo

Crear instalador que incluya:
1. El .exe
2. Instalador de Ansible
3. Scripts de configuración

**Herramientas recomendadas:**
- **Inno Setup** (gratis, fácil)
- **NSIS** (gratis, potente)
- **WiX Toolset** (Microsoft, profesional)

### Opción 3: Empaquetado ZIP

Crear ZIP con:
- `IT-Ops-CLI.exe`
- `INSTALACION.txt` (instrucciones)
- Scripts de instalación si es necesario

## 🔧 Troubleshooting

### "ModuleNotFoundError" al ejecutar .exe

**Solución**: Agregar el módulo faltante a `hiddenimports` en `build_exe.py`

### "File not found" para inventory/playbooks

**Solución**: Verificar que los archivos estén en `--add-data`. PyInstaller los extrae a un directorio temporal.

### El .exe no encuentra ansible.cfg

**Solución**: El código ya está adaptado para buscar archivos relativos al ejecutable cuando corre desde .exe.

### Ansible no se encuentra

**Solución**: El usuario debe instalar Ansible por separado:
```bash
pip install ansible
# O desde repositorio de Windows
```

## ✅ Ventajas del Ejecutable

1. **Protección básica del código** - No es fácilmente legible
2. **Fácil distribución** - Un solo archivo
3. **No requiere Python instalado** - Incluye Python runtime
4. **Instalación simple** - Solo ejecutar el .exe
5. **Portabilidad** - Funciona en cualquier Windows con requisitos

## ⚡ Comandos Rápidos

```bash
# Instalar PyInstaller
pip install pyinstaller

# Construir ejecutable
python build_exe.py

# Probar ejecutable
dist/IT-Ops-CLI.exe
```

## 📝 Notas Finales

- El ejecutable es **autocontenido** (incluye Python y dependencias)
- El código está **parcialmente protegido** (bytecode compilado)
- Ansible debe estar **instalado por separado** en el sistema destino
- El vault.yml se incluye si existe, **revisar seguridad** antes de distribuir

**¡Listo para compilar!** 🎉
