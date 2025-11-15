# Script PowerShell para configurar WinRM rápidamente
# Ejecutar como Administrador en el equipo remoto

Write-Host "🔧 Configurando WinRM..." -ForegroundColor Cyan

# Habilitar WinRM
Write-Host "  → Habilitando PSRemoting..." -ForegroundColor Yellow
Enable-PSRemoting -Force

# Configurar autenticación básica
Write-Host "  → Configurando autenticación básica..." -ForegroundColor Yellow
Set-Item WSMan:\localhost\Service\Auth\Basic -Value $true
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true

# Configurar firewall
Write-Host "  → Configurando firewall..." -ForegroundColor Yellow
netsh advfirewall firewall add rule name="WinRM HTTP" dir=in action=allow protocol=TCP localport=5985 2>$null
netsh advfirewall firewall add rule name="WinRM HTTPS" dir=in action=allow protocol=TCP localport=5986 2>$null

# Configurar TrustedHosts (para pruebas - acepta cualquier host)
Write-Host "  → Configurando TrustedHosts (modo prueba)..." -ForegroundColor Yellow
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

# Reiniciar servicio
Write-Host "  → Reiniciando servicio WinRM..." -ForegroundColor Yellow
Restart-Service WinRM

# Verificar estado
Write-Host "`n✅ WinRM configurado correctamente!" -ForegroundColor Green
Write-Host "`n📊 Estado del servicio:" -ForegroundColor Cyan
Get-Service WinRM | Format-Table -AutoSize

Write-Host "`n🧪 Para probar desde otro equipo, ejecutá:" -ForegroundColor Yellow
Write-Host "   Test-WSMan -ComputerName $env:COMPUTERNAME -Authentication Basic" -ForegroundColor White
Write-Host "`n⚠️  NOTA: Esta configuración es para PRUEBAS. Para producción, configurá TrustedHosts específicos." -ForegroundColor Yellow

