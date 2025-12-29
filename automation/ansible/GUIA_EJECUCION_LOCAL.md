# 🚀 Guía: Ejecutar Ansible en tu Equipo Local

Esta guía te explica cómo instalar y ejecutar Ansible en tu propio equipo Windows para probar los playbooks.

## 📋 Paso 1: Instalar Python (si no lo tenés)

Ansible requiere Python. Verificá si lo tenés:

```powershell
python --version
```

Si no lo tenés, descargalo desde: https://www.python.org/downloads/
- ✅ **IMPORTANTE**: Durante la instalación, marcá "Add Python to PATH"

## 📦 Paso 2: Instalar Ansible

Abrí PowerShell como **Administrador** y ejecutá:

```powershell
# Instalar Ansible y el módulo para Windows
pip install ansible pywinrm

# Verificar que se instaló correctamente
ansible --version
```

Si `pip` no funciona, probá:
```powershell
python -m pip install ansible pywinrm
```

## ⚙️ Paso 3: Configurar WinRM en tu Equipo (Opcional para localhost)

Para ejecutar en **localhost**, técnicamente no necesitás WinRM, pero si querés probar la conexión completa:

```powershell
# Ejecutar como Administrador
Enable-PSRemoting -Force
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true
```

## 🎯 Paso 4: Ejecutar el Playbook en Localhost

### Opción A: Usando el inventory de localhost (Recomendado)

```powershell
# Navegar a la carpeta de ansible
cd C:\Users\griedel\Downloads\Scripts-Laburo\automation\ansible

# Ejecutar el playbook de desinstalar
ansible-playbook -i inventory/hosts.localhost playbooks/software/desistalar.yml
```

### Opción B: Especificar localhost directamente

```powershell
cd C:\Users\griedel\Downloads\Scripts-Laburo\automation\ansible

ansible-playbook -i "localhost," -c local playbooks/software/desistalar.yml
```

### Opción C: Modificar el playbook para usar conexión local

Si tenés problemas, podés modificar temporalmente el playbook cambiando:
- `win_shell` por `shell` (pero esto puede no funcionar bien en Windows)
- O usar `ansible_connection=local` en el inventory

## 🔍 Ejemplo: Desinstalar Dell Command

Cuando ejecutés el playbook, te va a preguntar:

```
Nombre del software a desinstalar: Dell Command
Publisher del software (opcional): Dell Inc.
```

## 🐛 Solución de Problemas

### Error: "winrm or requests is not installed"
```powershell
pip install pywinrm requests
```

### Error: "No module named 'ansible'"
```powershell
# Verificar que Python esté en el PATH
python --version

# Reinstalar Ansible
pip install --upgrade ansible pywinrm
```

### Error: "win_shell requires WinRM"
Para localhost, podés crear un playbook alternativo que use `command` o modificar el inventory.

### El playbook no encuentra el software
- Verificá que el nombre sea correcto (búsqueda parcial)
- Probá solo con el nombre sin el publisher
- Ejecutá primero `ListarAplicaicones.yml` para ver qué software tenés instalado

## 📝 Comandos Útiles

### Verificar conexión a localhost
```powershell
ansible localhost -i "localhost," -c local -m win_ping
```

### Ejecutar un comando simple
```powershell
ansible localhost -i "localhost," -c local -m win_shell -a "Get-Date"
```

### Listar aplicaciones instaladas
```powershell
cd C:\Users\griedel\Downloads\Scripts-Laburo\automation\ansible
ansible-playbook -i inventory/hosts.localhost playbooks/software/ListarAplicaicones.yml
```

## 💡 Alternativa: Ejecutar PowerShell Directamente

Si Ansible te da problemas, podés ejecutar los comandos PowerShell directamente:

1. Abrí PowerShell como Administrador
2. Copiá y pegá los comandos de la sección "CÓMO PROBAR MANUALMENTE" del playbook
3. Modificá las variables según necesites

## 📚 Más Información

- Documentación oficial de Ansible: https://docs.ansible.com/
- Ansible para Windows: https://docs.ansible.com/ansible/latest/os_guide/windows.html

