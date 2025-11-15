# 🧪 Guía de Pruebas

Esta guía te ayuda a probar las herramientas, especialmente el forzador de 5GHz.

## 📋 Antes de Empezar

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Verificar PsExec:**
   - Asegurate de tener `PsExec.exe` en el PATH o en el directorio del script
   - Podés descargarlo de: https://docs.microsoft.com/en-us/sysinternals/downloads/psexec

3. **Configurar credenciales (opcional):**
   - Copiá `config.json.example` a `config.json`
   - Configurá tus credenciales de administrador

## 🔧 Configurar WinRM (Opcional - Solo para Ansible)

Si querés probar Ansible después:

1. **En el equipo remoto**, ejecutá como Administrador:
```powershell
.\automation\setup_winrm.ps1
```

O seguí la guía completa en `automation/WINRM_SETUP.md`

## 🧪 Probar el Forzador de 5GHz

### Paso 1: Verificar conexión actual

Primero, analizá el Wi-Fi del equipo para ver en qué banda está:

```bash
cd automation/python/wifi
python wifi_analyzer.py
```

Ingresá el inventario del equipo (ej: `NB036595`)

Esto te mostrará:
- SSID actual
- Banda actual (2.4 GHz o 5 GHz)
- Señal, canal, etc.

### Paso 2: Forzar conexión a 5GHz

```bash
python wifi_force_5ghz.py
```

1. Seleccioná opción `1` (Windows)
2. Ingresá el inventario (ej: `NB036595`)
3. Si querés, ingresá el SSID específico, o dejá en blanco para usar el actual

El script hará:
- ✅ Verificar si ya está en 5GHz
- ✅ Configurar preferencia de banda en el registro
- ✅ Desconectar y reconectar Wi-Fi
- ✅ Verificar resultado

### Paso 3: Verificar resultado

Después de ejecutar, el script te mostrará:
- Banda inicial vs banda final
- SSID actual
- Señal y canal

También podés ejecutar `wifi_analyzer.py` nuevamente para confirmar.

## 🔍 Qué Esperar

### Caso Exitoso:
```
✅ NB036595: Conectado a MiRed en 5 GHz
```

### Si no funciona:
- El script intentará múltiples métodos
- Revisá el reporte JSON en `data/reports/`
- Algunos adaptadores/drivers no permiten forzar banda específica

## 🐛 Solución de Problemas

### Error: "No se puede conectar con PsExec"

1. Verificar que el equipo esté encendido y en red
2. Verificar credenciales en `config.json`
3. Verificar firewall (debe permitir conexiones remotas)

### El script dice "OK" pero sigue en 2.4GHz

Algunos adaptadores/drivers no respetan la preferencia de banda. En ese caso:
- El script hizo lo posible
- Podrías necesitar configurar esto desde el router/WLC
- O usar políticas de grupo de Windows

### Error: "Adaptador no encontrado"

- Verificar que el equipo tenga Wi-Fi habilitado
- Algunos equipos usan nombres diferentes para el adaptador

## 📊 Ver Reportes

Todos los resultados se guardan en `data/reports/`:

```bash
# Ver reportes de análisis Wi-Fi
ls data/reports/wifi_analysis_*.json

# Ver reportes de forzado 5GHz
ls data/reports/wifi_force_5ghz_*.json
```

## 🎯 Probar Otros Scripts

### Reparación OneDrive:
```bash
cd automation/python/remediation
python onedrive_fix.py
```

### Reparación Outlook:
```bash
python outlook_fix.py
```

### Reparación VPN:
```bash
python vpn_fix.py
```

### Reparación SCCM:
```bash
python sccm_fix.py
```

## 💡 Tips

1. **Empezá con un equipo de prueba** que puedas ver físicamente
2. **Revisá los logs** en `data/logs/` si algo falla
3. **Usá el dashboard** para ver resultados visuales:
```bash
cd automation/python/dashboard
streamlit run simple_dashboard.py
```

## 📝 Notas

- Los scripts son **no destructivos** - no borran datos importantes
- Siempre generan reportes para auditoría
- Los logs ayudan a diagnosticar problemas

