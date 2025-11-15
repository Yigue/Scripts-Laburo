# 🔧 Guía de Configuración WinRM

Esta guía te explica cómo configurar WinRM en Windows para usar Ansible (opcional, para el futuro). **Por ahora, los scripts de Python con PsExec funcionan sin WinRM**.

## 📋 ¿Qué es WinRM?

WinRM (Windows Remote Management) permite ejecutar comandos remotos en Windows de forma similar a SSH en Linux. Es necesario para usar Ansible con Windows.

## 🚀 Configuración Rápida (Un Solo Equipo)

### Opción 1: Script PowerShell Automático (Recomendado)

Ejecutá este script PowerShell **en el equipo remoto** (como Administrador):

```powershell
# Habilitar WinRM
Enable-PSRemoting -Force

# Configurar WinRM para aceptar conexiones
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true

# Configurar firewall
netsh advfirewall firewall add rule name="WinRM HTTP" dir=in action=allow protocol=TCP localport=5985
netsh advfirewall firewall add rule name="WinRM HTTPS" dir=in action=allow protocol=TCP localport=5986

# Configurar para aceptar conexiones de cualquier IP (solo para pruebas)
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

# Reiniciar servicio WinRM
Restart-Service WinRM

Write-Host "✅ WinRM configurado correctamente" -ForegroundColor Green
```

### Opción 2: Comandos Manuales

1. **Abrir PowerShell como Administrador** en el equipo remoto

2. **Habilitar PSRemoting:**
```powershell
Enable-PSRemoting -Force
```

3. **Configurar autenticación básica:**
```powershell
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true
```

4. **Configurar Firewall:**
```powershell
netsh advfirewall firewall add rule name="WinRM HTTP" dir=in action=allow protocol=TCP localport=5985
```

5. **Configurar TrustedHosts (para pruebas):**
```powershell
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
```

6. **Reiniciar WinRM:**
```powershell
Restart-Service WinRM
```

## 🧪 Verificar Configuración

### Desde el Equipo Remoto:

```powershell
# Ver estado de WinRM
Get-Service WinRM

# Ver configuración
winrm get winrm/config
```

### Desde tu PC (para probar conexión):

```powershell
# Probar conexión
Test-WSMan -ComputerName NOMBRE_DEL_EQUIPO -Authentication Basic

# O con winrm
winrm id -r:NOMBRE_DEL_EQUIPO -auth:basic -u:Administrador -p:TU_PASSWORD
```

## 🔐 Configuración con Dominio (Más Seguro)

Si estás en un dominio, podés usar Kerberos en lugar de Basic:

```powershell
# En el equipo remoto
Enable-PSRemoting -Force
Set-Item WSMan:\localhost\Service\Auth\Kerberos -Value $true
Set-Item WSMan:\localhost\Service\Auth\Negotiate -Value $true

# En tu PC (para usar con Ansible)
# No necesitás TrustedHosts si usás Kerberos
```

## 📝 Configurar Ansible (Opcional)

Una vez que WinRM esté configurado, podés usar Ansible:

1. **Instalar Ansible:**
```bash
pip install ansible pywinrm
```

2. **Configurar inventory** (`automation/ansible/inventory/hosts`):
```ini
[windows_hosts]
NB036595 ansible_host=NB036595 ansible_user=Administrador ansible_password=TU_PASSWORD ansible_connection=winrm ansible_winrm_transport=ntlm
NB046068 ansible_host=NB046068 ansible_user=Administrador ansible_password=TU_PASSWORD ansible_connection=winrm ansible_winrm_transport=ntlm
```

3. **Probar conexión:**
```bash
cd automation/ansible
ansible windows_hosts -i inventory/hosts -m win_ping
```

## ⚠️ Notas de Seguridad

- **Para producción:** No uses `AllowUnencrypted` y configura TrustedHosts específicos
- **Para pruebas:** Está bien usar la configuración básica
- **Firewall:** Asegurate de que el puerto 5985 esté abierto solo en redes internas

## 🐛 Solución de Problemas

### Error: "No se puede conectar"

1. Verificar que WinRM esté corriendo:
```powershell
Get-Service WinRM
```

2. Verificar firewall:
```powershell
netsh advfirewall firewall show rule name="WinRM HTTP"
```

3. Verificar que el equipo esté accesible:
```powershell
Test-NetConnection -ComputerName NOMBRE_DEL_EQUIPO -Port 5985
```

### Error: "Acceso denegado"

- Verificar credenciales
- Verificar que el usuario tenga permisos de administrador
- Si usás dominio, probar con `ansible_winrm_transport=kerberos`

## 💡 Recomendación

**Por ahora, usá los scripts de Python con PsExec** que ya funcionan sin configuración adicional. WinRM es útil cuando querés automatizar muchos equipos a la vez con Ansible.

