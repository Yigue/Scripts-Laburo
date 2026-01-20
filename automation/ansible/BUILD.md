# 📦 Guía para Crear Ejecutable .exe

## Opciones Disponibles

### Opción 1: PyInstaller (Recomendado) ✅

**PyInstaller** es la herramienta más popular y confiable para crear ejecutables de Python.

#### Instalación

```bash
pip install pyinstaller
```

#### Método 1: Usando el script build_exe.py (Más fácil) ⭐

```bash
python build_exe.py
```

El ejecutable se generará en `dist/IT-Ops-CLI.exe`

#### Método 2: Usando el archivo .spec (Más personalizable)

```bash
pyinstaller IT-Ops-CLI.spec
```

#### Método 3: Comando directo (Básico)

**Windows:**
```bash
pyinstaller --onefile --name=IT-Ops-CLI --add-data "inventory;inventory" --add-data "playbooks;playbooks" --add-data "roles;roles" --add-data "ansible.cfg;." app.py
```

**Linux/Mac:**
```bash
pyinstaller --onefile --name=IT-Ops-CLI --add-data "inventory:inventory" --add-data "playbooks:playbooks" --add-data "roles:roles" --add-data "ansible.cfg:." app.py
```

**Nota**: En Windows usa `;` y en Linux/Mac usa `:` para `--add-data`.

### Opción 2: cx_Freeze (Alternativa)

```bash
pip install cx_Freeze
```

Crear archivo `setup_cx.py`:

```python
from cx_Freeze import setup, Executable

setup(
    name="IT-Ops-CLI",
    version="1.0",
    description="IT-Ops CLI - Automatización con Ansible",
    executables=[Executable("app.py", base=None)],
    options={
        "build_exe": {
            "include_files": ["inventory/", "playbooks/", "roles/", "ansible.cfg"],
            "packages": ["cli", "questionary", "rich", "yaml"],
        }
    }
)
```

Luego ejecutar:
```bash
python setup_cx.py build
```

### Opción 3: Nuitka (Compila a C++, más rápido)

```bash
pip install nuitka
python -m nuitka --onefile --include-data-dir=inventory=inventory --include-data-dir=playbooks=playbooks --include-data-dir=roles=roles app.py
```

## Configuración Recomendada

### Para Producción (Ocultar Consola)

Editar `IT-Ops-CLI.spec` o `build_exe.py` y descomentar:
```python
'--windowed',  # Sin consola
```

O usar:
```bash
pyinstaller --onefile --windowed --name=IT-Ops-CLI ...
```

### Para Debugging (Ver Consola) ⭐ Recomendado para pruebas

```bash
pyinstaller --onefile --console --name=IT-Ops-CLI ...
```

O mantener comentado `--windowed` en `build_exe.py` (por defecto muestra consola).

## Archivos Incluidos

El ejecutable incluirá automáticamente:
- ✅ Todo el código Python (cli/, app.py)
- ✅ `inventory/` (con group_vars y vault)
- ✅ `playbooks/`
- ✅ `roles/`
- ✅ `ansible.cfg`

## Consideraciones de Seguridad

### ⚠️ Importante sobre el Vault

El archivo `inventory/group_vars/all/vault.yml` **SÍ se incluirá** en el .exe si está presente.

**Recomendaciones:**
1. **NO incluir vault.yml en el repositorio** (agregar a .gitignore)
2. **Usar variables de entorno** para secretos en producción
3. **El usuario debe proporcionar su propio vault.yml** externamente
4. **O excluir manualmente** del .exe editando `build_exe.py`

### Excluir Archivos Sensibles

Modificar `build_exe.py` para excluir:

```python
# Agregar después de definir datas:
# Filtrar vault.yml
datas = [(src, dst) for src, dst in datas if 'vault.yml' not in src]
```

## Tamaño del Ejecutable

- **Con PyInstaller --onefile**: ~50-100 MB (incluye Python runtime)
- **Con PyInstaller --onedir**: ~30-50 MB en carpeta dist/
- **Con Nuitka**: ~20-40 MB (más optimizado)

## Dependencias Externas

El ejecutable necesita:
- ✅ **Ansible instalado** en el sistema (o incluirlo en el paquete)
- ✅ **PowerShell** (para scripts remotos)
- ✅ **WinRM habilitado** en hosts destino

**Nota**: Ansible NO se puede empaquetar fácilmente, el usuario debe tenerlo instalado.

### Solución: Instalador Completo

Puedes crear un instalador que incluya:
1. El ejecutable .exe
2. Instalador de Ansible
3. Scripts de configuración

Herramientas para instaladores:
- **Inno Setup** (Windows)
- **NSIS** (Windows)
- **WiX Toolset** (Windows)

## Proceso Recomendado

1. **Instalar PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Construir ejecutable**:
   ```bash
   python build_exe.py
   ```

3. **Probar el .exe**:
   ```bash
   dist/IT-Ops-CLI.exe
   ```

4. **Distribuir**:
   - El archivo `dist/IT-Ops-CLI.exe` es autocontenido
   - Asegurarse que Ansible esté instalado en el sistema destino
   - Incluir instrucciones de instalación si es necesario

## Troubleshooting

### Error: "ModuleNotFoundError"
Agregar al `hiddenimports` en `build_exe.py` o `.spec`.

### Error: "File not found" al ejecutar .exe
Verificar que los archivos de datos (inventory, playbooks) estén incluidos en `--add-data`.

**Nota**: PyInstaller extrae archivos a un directorio temporal. El código debe usar rutas relativas al ejecutable.

### El .exe es muy grande
Usar `--onedir` en lugar de `--onefile` o excluir módulos innecesarios.

### El .exe no funciona
Ejecutar desde consola para ver errores (quitar `--windowed` o usar `--console`).

### Ansible no se encuentra
El ejecutable NO incluye Ansible. El usuario debe instalarlo por separado.

## Protección del Código

### ✅ Lo que SÍ protege PyInstaller:
- Código Python compilado a bytecode (.pyc)
- No es fácilmente legible sin herramientas especializadas
- Reduce la exposición del código fuente

### ⚠️ Lo que NO protege completamente:
- Python bytecode puede ser decompilado
- Para protección real necesitas:
  - **Obfuscación** adicional (pyarmor, etc.)
  - **Compilación a C++** (Nuitka)
  - **Licencias comerciales** para protección avanzada

### Recomendación:
Para protección básica, PyInstaller es suficiente. Para protección avanzada, considerar **PyArmor** o **Nuitka**.
