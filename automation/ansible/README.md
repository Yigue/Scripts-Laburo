# Ansible - Configuración y Uso

Esta carpeta contiene playbooks de Ansible para automatización masiva. **Actualmente son templates** que requieren configuración adicional.

## Requisitos Previos

### 1. Instalar Ansible

```bash
pip install ansible pywinrm
```

### 2. Configurar WinRM en Hosts Remotos

Para usar Ansible con Windows, necesitás configurar WinRM en cada host:

```powershell
# Ejecutar en cada host Windows (como Administrador)
Enable-PSRemoting -Force
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true
```

### 3. Configurar Inventory

1. Copiá `inventory/hosts.example` a `inventory/hosts`
2. Agregá tus hosts con credenciales:

```ini
[windows_hosts]
NB036595 ansible_host=NB036595 ansible_user=Administrador ansible_password=password
NB046068 ansible_host=NB046068 ansible_user=Administrador ansible_password=password
```

## Uso

Una vez configurado, podés ejecutar playbooks:

```bash
cd automation/ansible
ansible-playbook -i inventory/hosts playbooks/remediation/onedrive_fix.yml
```

## Nota Importante

**Por ahora, usá los scripts de Python con PsExec** que ya están funcionando. Ansible es para automatización masiva futura cuando tengas WinRM configurado en todos los hosts.

