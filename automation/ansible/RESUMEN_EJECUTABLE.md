# ✅ Sistema de Compilación a .exe Implementado

## Archivos Creados

### 1. `build_exe.py` ⭐
Script automatizado para construir el .exe con PyInstaller.

**Uso:**
```bash
pip install pyinstaller
python build_exe.py
```

**Características:**
- ✅ Un solo archivo .exe (~50-100 MB)
- ✅ Incluye todas las dependencias Python
- ✅ Incluye inventory/, playbooks/, roles/, ansible.cfg
- ✅ Detecta automáticamente el OS (Windows/Linux/Mac)
- ✅ Configuración optimizada para reducir tamaño

### 2. `IT-Ops-CLI.spec`
Archivo de especificación de PyInstaller para personalización avanzada.

**Uso:**
```bash
pyinstaller IT-Ops-CLI.spec
```

### 3. Modificaciones en el Código

**`cli/shared/config.py`:**
- ✅ Detecta si se ejecuta desde .exe (`sys.frozen`)
- ✅ Usa directorio del ejecutable cuando corre desde .exe
- ✅ Busca archivos relativos al ejecutable

**`cli/infrastructure/logging/debug_logger.py`:**
- ✅ Detecta ejecución desde .exe
- ✅ Crea logs en directorio del ejecutable

## Cómo Usar

### Método 1: Script Automatizado (Recomendado) ⭐

```bash
# 1. Instalar PyInstaller
pip install pyinstaller

# 2. Ejecutar script de construcción
python build_exe.py

# 3. El .exe estará en dist/IT-Ops-CLI.exe
dist/IT-Ops-CLI.exe
```

### Método 2: Comando Directo

**Windows:**
```bash
pyinstaller --onefile --name=IT-Ops-CLI --add-data "inventory;inventory" --add-data "playbooks;playbooks" --add-data "roles;roles" --add-data "ansible.cfg;." app.py
```

**Linux/Mac:**
```bash
pyinstaller --onefile --name=IT-Ops-CLI --add-data "inventory:inventory" --add-data "playbooks:playbooks" --add-data "roles:roles" --add-data "ansible.cfg:." app.py
```

## ⚠️ Consideraciones Importantes

### 1. Ansible NO se Incluye
El .exe **NO incluye Ansible**. El usuario debe tenerlo instalado:
```bash
pip install ansible
```

### 2. Seguridad del Vault
Si existe `inventory/group_vars/all/vault.yml`, se incluirá en el .exe.

**Recomendación:** Excluir vault.yml o usar variables de entorno.

### 3. Tamaño
El .exe será aproximadamente **50-100 MB** (incluye Python + dependencias).

## 🔒 Protección del Código

### Nivel de Protección: **Básico-Medio**
- ✅ Código compilado a bytecode (.pyc)
- ✅ No es fácilmente legible sin herramientas
- ⚠️ Puede ser decompilado con herramientas especializadas

### Para Mayor Protección:
- **PyArmor**: Obfuscación adicional
- **Nuitka**: Compilación a C++

## 📦 Distribución

### Opción Simple:
Distribuir solo `dist/IT-Ops-CLI.exe`

### Opción Completa:
Crear instalador con:
- El .exe
- Instalador de Ansible
- Scripts de configuración

**Herramientas:** Inno Setup, NSIS, WiX Toolset

## ✅ Estado Actual

✅ Script de construcción creado
✅ Código adaptado para ejecución desde .exe
✅ Documentación completa
✅ Configuración optimizada

**¡Listo para compilar!** 🎉
