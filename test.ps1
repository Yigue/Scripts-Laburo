#------------------------------------------------RECURSOS PXE
$Origen = "\\pc101338\c$\iTools\PSTools"
$Destino = "C:\PSTools"
$RutaEquipos = "\\pc101338\c$\iTools\EquiposAutorizados.txt"


# Verificar que el archivo existe
if (-not (Test-Path $RutaEquipos)) {
    Write-Host "No se encontró el archivo en $RutaEquipos" -ForegroundColor Red
    exit
}

# Leer los equipos (ignora líneas vacías)
$equiposAutorizados = Get-Content $RutaEquipos | Where-Object { $_.Trim() -ne "" }

# Obtener nombre del equipo actual
$miEquipo = $env:COMPUTERNAME

# Validar autorización
if ($miEquipo -notin $equiposAutorizados) {
    cls
    Write-Host "El equipo $miEquipo no está autorizado para ejecutar este script." -ForegroundColor Red
    Read-Host "Presiona ENTER para continuar"
    exit
}
else {
    cls
    Write-Host "Equipo autorizado." -ForegroundColor Green
}


# Verificar si la carpeta de destino ya existe
if (-Not (Test-Path -Path $Destino)) {
    try {
        Copy-Item -Path $Origen -Destination $Destino -Recurse -Force
        Write-Host "Carpeta copiada exitosamente a $Destino"
        reg add "HKCU\Software\Sysinternals\PsExec" /v EulaAccepted /t REG_DWORD /d 1 /f
    }
    catch {
        Write-Host "Error al copiar la carpeta: $_"
        Read-Host "Presiona ENTER para continuar"
        exit
    }
}
else {
    Write-Host "PsExec instalado"
}

$bandera = $false 
$TEMP = $false
$path = Get-Location
$Seleccion = 1
$RemotePC = Read-Host "Inventario"
$FilePID = (Get-Process -name Asistente-TI | Where-Object { $_.MainWindowTitle -eq 'Asistente-TI' -replace '\.[^.]*$', '' }).Id
$IsAdministrator = ([Security.Principal.WindowsPrincipal] `
                   [Security.Principal.WindowsIdentity]::GetCurrent() `
                   ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

cls


while ($bandera -eq $false){
    # Verificar la conexión al equipo remoto
    if (Test-Connection -ComputerName $RemotePC -Count 2 -Quiet) {
        Write-Host "Conexión exitosa con $RemotePC."
        $bandera = $true

        try {
            Write-Host "Estableciendo ExecutionPolicy en $RemotePC..." -ForegroundColor Cyan

            $cmd1 = psexec \\$RemotePC powershell -Command "Set-ExecutionPolicy RemoteSigned -Force"
            $cmd2 = psexec \\$RemotePC powershell -Command "Set-ExecutionPolicy RemoteSigned -Force"

            Write-Host "ExecutionPolicy actualizado correctamente en $RemotePC" -ForegroundColor Green
        }
        catch {
            Write-Host "Error al actualizar ExecutionPolicy en $RemotePC" -ForegroundColor Red
            Write-Host "Detalles: $($_.Exception.Message)" -ForegroundColor Yellow
        }


        # Verificar si la carpeta Temp existe en el equipo remoto
            Invoke-Command -ComputerName $RemotePC -ScriptBlock {
                $folder = "C:\TEMP"
                if (!(Test-Path $folder)) {
                    New-Item -Path $folder -ItemType Directory -Force
                }
            }
    } else {
        Write-Host "No se pudo conectar con $RemotePC. Verifique la conexión."
        $RemotePC = Read-Host "Inventario"
        Read-Host "Presiona ENTER para continuar"
    }
}



while ($true) {

cls

$IPadress = ipconfig|FINDSTR "Dirección IPv4"
$SSID = (get-netconnectionProfile).Name

Write-Host "
              ░█████╗░███╗░░██╗██████╗░██████╗░███████╗░█████╗░███╗░░██╗██╗
              ██╔══██╗████╗░██║██╔══██╗██╔══██╗██╔════╝██╔══██╗████╗░██║██║
              ███████║██╔██╗██║██║░░██║██████╔╝█████╗░░███████║██╔██╗██║██║
              ██╔══██║██║╚████║██║░░██║██╔══██╗██╔══╝░░██╔══██║██║╚████║██║
              ██║░░██║██║░╚███║██████╔╝██║░░██║███████╗██║░░██║██║░╚███║██║
              ╚═╝░░╚═╝╚═╝░░╚══╝╚═════╝░╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝╚═╝░░╚══╝╚═╝

                       Bienvenido al Asistente de Soporte Tecnico

                 Por favor, a continuacion ingrese la opcion a ejecutar:
                
                  Equipo Remoto .  .  .  .  .  : $RemotePC   

             " -ForegroundColor RED

 "

  1. Mostrar especificaciones             8. Instalar Office          
  2. Terminar de configurar               9. Instalar Impresora                        
  3. Optimizar                            10. Calibrar Zebra Wifi   
  4. Reiniciar                            11. Aplicaciones
  5. Actualizar drivers DELL                       
  6. WCORP (Scrip, cleanDNS, GPUPDATE) 
  7. Activar windows             

  0. Otro equipo
  
 "


$Seleccion = Read-Host "Selecciona una Opcion"

cls

switch ( $Seleccion )
{
        
    1 {Invoke-Command -ComputerName $RemotePC -ScriptBlock {

        # 1) OBTENER LAS EXPECIFICACIONES DEL SISTEMA

        $systemInfo = Get-CimInstance -ClassName Win32_ComputerSystem
        $biosInfo = Get-CimInstance -ClassName Win32_BIOS
        $processorInfo = Get-CimInstance -ClassName Win32_Processor
        $osInfo = Get-WmiObject -Class Win32_OperatingSystem
        $serialNumber = Get-WmiObject -Class Win32_BIOS | Select-Object -ExpandProperty SerialNumber
        $path = "Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\Packages"

        $pkgs = Get-ChildItem $path | Where-Object { $_.Name -match "Package_for_RollupFix" } | Sort-Object Name -Descending | Select-Object -First 1

        

        # Obtener el modelo y la capacidad del disco
        $diskInfo = Get-CimInstance -ClassName Win32_DiskDrive | Select-Object Model, @{Name="Size(GB)";Expression={[math]::round($_.Size / 1GB, 2)}}

        # Obtener información sobre las particiones de disco y el espacio libre
        $logicalDisks = Get-CimInstance -ClassName Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 }

        # Obtener todas las IP habilitadas y clasificar según el tipo de adaptador
        $networkAdapters = Get-CimInstance -ClassName Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled -eq $true }

        # Obtener la IP del adaptador Wi-Fi
        $wifiAdapter = $networkAdapters | Where-Object { $_.Description -match "Wi-Fi|Wireless" }
        $wifiIP = if ($wifiAdapter -and $wifiAdapter.IPAddress) { $wifiAdapter.IPAddress -join ', ' } else { "No conectado a Wi-Fi" }

        # Obtener la IP del adaptador Ethernet (excluyendo el adaptador Wi-Fi)
        $ethernetAdapter = $networkAdapters | Where-Object { $_.Description -notmatch "Wi-Fi|Wireless" }
        $ethernetIP = if ($ethernetAdapter -and $ethernetAdapter.IPAddress) { $ethernetAdapter.IPAddress -join ', ' } else { "No conectado a Ethernet" }

        # Obtener la versión de actualización y compilación desde el sistema operativo
        $displayVersion = Get-ItemPropertyValue -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' -Name DisplayVersion
        $buildNumber = $osInfo.BuildNumber
        
        # Formatear la información como la de "winver"
        $versionWinver = $pkgs.PSChildName -replace ".*~", ""

        # Obtener la fecha de instalación de Windows y convertirla a un formato legible
        $windowsInstallDate = (Get-WmiObject -Class Win32_OperatingSystem).InstallDate
        $formattedInstallDate = [Management.ManagementDateTimeConverter]::ToDateTime($windowsInstallDate).ToString("dd/MM/yyyy HH:mm:ss")

        # Mostrar información del sistema de forma organizada
        $systemSpecs = @"
        =========================================================
                       ESPECIFICACIONES DEL SISTEMA
        =========================================================
        - Nombre del equipo       : $($systemInfo.Name)
        - Modelo del equipo       : $($systemInfo.Model)
        - Fabricante              : $($systemInfo.Manufacturer)
        - Número de Serie (BIOS)  : $serialNumber
        - Procesador              : $($processorInfo.Name)
        - Cantidad de RAM (GB)    : $([math]::round($systemInfo.TotalPhysicalMemory / 1GB, 2))
        - Versión de BIOS         : $($biosInfo.SMBIOSBIOSVersion)
        - Sistema Operativo       : $($osInfo.Caption)
        - Winver (Detalles SO)    : $versionWinver
        - Fecha de Instalación    : $formattedInstallDate
        - Dirección IP (Wi-Fi)    : $wifiIP
        - Dirección IP (Ethernet) : $ethernetIP

        =========================================================
                         INFORMACIÓN DEL DISCO
        =========================================================

"@

        $diskInfo | ForEach-Object {
            $disk = $_

            $systemSpecs += "        Modelo del Disco      : $($disk.Model)`n"
            $systemSpecs += "        Tamaño del Disco (GB) : $($disk.'Size(GB)')`n"

            $logicalDisks | ForEach-Object {
                $ld = $_

                if ($disk.DeviceID -eq $ld.DeviceID) {
                    $freeSpaceGB = [math]::round($ld.FreeSpace / 1GB, 2)
                    $systemSpecs += "        Espacio Libre (GB)    : $freeSpaceGB`n"
                }
            }

            $systemSpecs += "`n"
        }

        return $systemSpecs

        }
        
        if ($RemotePC -match '^[Nn]') {
            
            write-host "       ========================================================="
            write-host "                         ESTADO DE BATERIA"
            write-host "       =========================================================" 
            Invoke-Command -ComputerName $RemotePC -ScriptBlock {
                # Generar el informe de batería en formato XML temporal
                $batteryXml = "$env:TEMP\battery.xml"
                powercfg /batteryreport /xml /output $batteryXml | Out-Null
    
                # Cargar el XML
                [xml]$xml = Get-Content $batteryXml
    
                # Extraer capacidades
                $designed = $xml.BatteryReport.Batteries.Battery.DesignCapacity
                $full     = $xml.BatteryReport.Batteries.Battery.FullChargeCapacity
    
                # Calcular salud
                $health = [math]::Round(($full / $designed) * 100, 2)
    
                # Determinar estado
                if ($health -ge 90) { $status = "Excellent" }
                elseif ($health -ge 70) { $status = "Good" }
                elseif ($health -ge 50) { $status = "Fair" }
                else { $status = "Poor" }
    
                # Borrar archivo temporal
                Remove-Item $batteryXml -Force -ErrorAction SilentlyContinue
    
                # Mostrar resultados
                [PSCustomObject]@{
                    ComputerName       = $env:COMPUTERNAME
                    DesignedCapacity   = "$designed mWh"
                    FullChargeCapacity = "$full mWh"
                    BatteryHealth      = "$health %"
                    Status             = $status
                }
    
            }
        }

        Read-Host "Presiona ENTER para continuar"
    }
    
    2 {

            #------------------------------------------------------------------------------------------------>COPIAR RECURSOS 

            $Origen = "\\pc101338\c$\iTools\Dell-Command-Update-Application_6VFWW_WIN_5.4.0_A00.EXE"
            $Destino = "\\$RemotePC\c$\temp"
            $PsExec = "C:\PSTools\PsExec.exe"  # Ruta local a PsExec
            $SourcePath = "\\pc101338\c$\iTools\Office"
            $SetupExe = "$SourcePath\setup.exe"
            $ConfigXml = "$SourcePath\config.xml"
    

            Write-Host "Copiando Instalador Dell Command..." -ForegroundColor Yellow
            Copy-Item -Path $Origen -Destination $Destino
            
            $Origen = "\\pc101338\c$\iTools\NoSleep.exe"
            
            Write-Host "Copiando NoSleep.exe a $RemotePC..." -ForegroundColor Yellow
            Copy-Item -Path $Origen -Destination $Destino -Force

            # Ruta de destino en el equipo remoto
            $RemotePath = "\\$RemotePC\c$\Temp"

            # Copiar archivos desde pc101338 hacia el equipo remoto
            Write-Host "Copiando setup.exe y config.xml a $RemotePC para instalacion de office 365..." -ForegroundColor Yellow
            try {
                Copy-Item $SetupExe -Destination $RemotePath -Force -ErrorAction Stop
                Copy-Item $ConfigXml -Destination $RemotePath -Force -ErrorAction Stop
            } catch {
                Write-Host "❌ Error al copiar archivos: $_" -ForegroundColor Red
                exit
            }

            
            # ------------------------------------------------------------------------------------------> Ejecutar NoSleep.exe en sesión interactiva (con PsExec)

            Write-Host "Ejecutando NoSleep.exe" -ForegroundColor Green
            Start-Process $PsExec -ArgumentList "-accepteula \\$RemotePC -i -d C:\temp\NoSleep.exe"


            # ------------------------------------------------------------------------------------------> Suspender BitLocker SI ES NB

            if ($RemotePC -match '^[Nn]') {
            # Suspender BitLocker en C: por 1 reinicio
                Suspend-BitLocker -MountPoint "C:" -RebootCount 1

                # Verificar estado
                Get-BitLockerVolume | Format-Table MountPoint, ProtectionStatus, VolumeStatus
            }
            # ------------------------------------------------------------------------------------------> ACTUALIZAR DRIVERS



            Invoke-Command -ComputerName $RemotePC -ScriptBlock {
            Write-Host "Validando si Dell Command está instalado..." -ForegroundColor Yellow

            $dellCommandInstalled = Get-ItemProperty -Path `
                'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*', `
                'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' `
                | Where-Object { $_.DisplayName -like "*Dell Command*Update*" }

            if ($dellCommandInstalled) {
                Write-Host "Dell Command ya está instalado." -ForegroundColor Green
            } else {
                Write-Host "Dell Command no está instalado. Instalando..." -ForegroundColor Yellow

                $installer = "C:\TEMP\Dell-Command-Update-Application_6VFWW_WIN_5.4.0_A00.EXE"
                $proc = Start-Process -FilePath $installer -ArgumentList "/s" -Wait -PassThru

                if ($proc.ExitCode -ne 0) {
                    Write-Host "❌ Instalación fallida con código $($proc.ExitCode)" -ForegroundColor Red
                    return
                } else {
                    Write-Host "✅ Instalación completada exitosamente." -ForegroundColor Green
                }
            }

            # Buscar dcu-cli
            $DCUPath = if (Test-Path "C:\Program Files (x86)\Dell\CommandUpdate\dcu-cli.exe") {
                "C:\Program Files (x86)\Dell\CommandUpdate\dcu-cli.exe"
            } elseif (Test-Path "C:\Program Files\Dell\CommandUpdate\dcu-cli.exe") {
                "C:\Program Files\Dell\CommandUpdate\dcu-cli.exe"
            } else {
                Write-Host "❌ Dell Command Update no encontrado." -ForegroundColor Red
                return
            }

            Write-Host "Ejecutando actualizaciones en segundo plano..." -ForegroundColor Yellow

            $logOut = "C:\TEMP\dcu-output.txt"
            $logErr = "C:\TEMP\dcu-error.txt"

            Start-Process -FilePath $DCUPath `
                -ArgumentList "/applyUpdates" `
                -WindowStyle Hidden `
                -RedirectStandardOutput $logOut `
                -RedirectStandardError $logErr `
                -Wait

            Write-Host "✅ Actualización finalizada. Mostrando logs..." -ForegroundColor Green

            # Mostrar logs
            Write-Host "`n--- Salida estándar (actualizaciones aplicadas): ---`n" -ForegroundColor Cyan
            Get-Content $logOut

            Write-Host "`n--- Errores (si hubo): ---`n" -ForegroundColor Magenta
            Get-Content $logErr

            }

            # --------------------------------------------------------------------------------------------->INSTALAR OFFICE
            # Validar si ya esta instalado Office
            Write-Host "Validando si office se encuentra ya instalado en $RemotePC..." -ForegroundColor Yellow

            $CheckOffice = Invoke-Command -ComputerName $RemotePC -ScriptBlock {
                Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" |
                Where-Object { $_.DisplayName -match "Microsoft 365|Office" } |
                Select-Object DisplayName, DisplayVersion
            }

            # Mostrar resultado
            if ($CheckOffice) {
                Write-Host "Office 365 esta instalado en $RemotePC. ✅" -ForegroundColor Green
                $CheckOffice | Format-Table -AutoSize
            } else {
                Write-Host "❌ No se encontró Office instalado en $RemotePC. Puede seguir instalándose o hubo un error." -ForegroundColor Red

                # Ejecutar instalación con PsExec
                Write-Host "Iniciando instalación silenciosa de Office 365 en $RemotePC..." -ForegroundColor Green
                Start-Process $PsExec -ArgumentList "\\$RemotePC -s -h cmd.exe /c `"C:\Temp\setup.exe /configure C:\Temp\config.xml`"" -Wait
            }

            # Esperar 5 minutos
            Write-Host "Validando instalación..." -ForegroundColor Yellow
            Start-Sleep -Seconds 30

            # Verificar si Office fue instalado
            Write-Host "Validando instalación en $RemotePC..." -ForegroundColor Cyan
            $CheckOffice = Invoke-Command -ComputerName $RemotePC -ScriptBlock {
                Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" |
                Where-Object { $_.DisplayName -match "Microsoft 365|Office" } |
                Select-Object DisplayName, DisplayVersion
            }

            # Mostrar resultado
            if ($CheckOffice) {
                Write-Host "✅ Office 365 instalado correctamente en $RemotePC." -ForegroundColor Green
                $CheckOffice | Format-Table -AutoSize
            } else {
                Write-Host "❌ No se encontró Office instalado en $RemotePC. Puede seguir instalándose o hubo un error." -ForegroundColor Red
            }

            #-------------------------------------------------------------------------------------------> ACTIVAR LICENCIA

            Invoke-Command -ComputerName $RemotePC -ScriptBlock {

            Write-Output "Activando licencia de Windows."
            
            slmgr.vbs /ipk P9BHN-HYVGH-DVK3V-JHPJ6-HFR9M
            slmgr.vbs /ipk 3BRT8-N267D-TXT8G-W2F7F-JHW4K
            slmgr.vbs /ipk 22JFY-NPQ9G-RQ6P2-9PYM7-2R6FT

            Write-Output "Licencia aplicada."
            
            }

            #------------------------------------------------------------------------------------------> SCANNOW

            Write-Host "Realizando sfc /Scannow en $RemotePC..." -ForegroundColor Cyan
            Start-Process "C:\PSTools\PsExec.exe" -ArgumentList "\\$RemotePC -s cmd /c `"sfc /scannow`"" -Wait

            Restart-Computer -ComputerName $remotePC -Force

            Write-Host "Se finalizo la configuracion 🎉" -ForegroundColor Green

            Read-Host "Presiona ENTER para continuar"


    }
    
    
    3 {Invoke-Command -ComputerName $RemotePC -ScriptBlock {

            # 3) OPTIMIZAR PCs - OK

            $users = Get-ChildItem "C:\Users" -Directory
            foreach ($user in $users) {
                $tempPath = "C:\Users\$($user.Name)\AppData\Local\Temp"
                if (Test-Path $tempPath) {
                    Remove-Item "$tempPath\*" -Force -Recurse -ErrorAction SilentlyContinue
                }
            }

            # 2. Vaciar todas las papeleras de reciclaje
            Clear-RecycleBin -Force -ErrorAction SilentlyContinue

            # 3. Liberar memoria caché del sistema
            Write-Output "Liberando memoria caché..."
            [System.GC]::Collect()
            [System.GC]::WaitForPendingFinalizers()

            # 4. Detener servicios innecesarios para mejorar el rendimiento
            $servicesToDisable = @("SysMain", "DiagTrack") # Superfetch, Telemetría,  "WSearch" Indexado
            foreach ($service in $servicesToDisable) {
                Stop-Service -Name $service -Force -ErrorAction SilentlyContinue
                Set-Service -Name $service -StartupType Disabled
            }

            # 5. Optimizar el almacenamiento
            Write-Output "Ejecutando optimización del disco..."
            Start-Process -FilePath "defrag.exe" -ArgumentList "/C /H /O" -NoNewWindow -Wait

            # 6. Eliminar caché innecesaria del sistema
            Remove-Item "C:\Windows\Temp\*" -Force -Recurse -ErrorAction SilentlyContinue
            Remove-Item "C:\Windows\Prefetch\*" -Force -Recurse -ErrorAction SilentlyContinue

            # 7. Reiniciar el explorador de Windows para aplicar cambios
            Stop-Process -Name "explorer" -Force -ErrorAction SilentlyContinue
            Start-Process "explorer.exe"
        }

        Write-Host "Realizando sfc /Scannow en $RemotePC..." -ForegroundColor Cyan

        Start-Process "C:\PSTools\PsExec.exe" -ArgumentList "\\$RemotePC -s cmd /c `"sfc /scannow`"" -Wait

        Write-Host "Optimización completada." -ForegroundColor Green

        Read-Host "Presiona ENTER para continuar"
    }
    
    4 { Invoke-Command -ComputerName $RemotePC -ScriptBlock {
            # Suspender BitLocker en C: por 1 reinicio
            Suspend-BitLocker -MountPoint "C:" -RebootCount 1

            # Verificar estado
            Get-BitLockerVolume | Format-Table MountPoint, ProtectionStatus, VolumeStatus
        }

        Restart-Computer -ComputerName $remotePC -Force -Wait -For PowerShell -Delay 10 -Timeout 600
        Write-Host "El reinicio de $remotePC se realizó exitosamente y el equipo está nuevamente en línea." -ForegroundColor Green
        Read-Host "Presiona ENTER para continuar"
        
      }
    
    5 {
            $Origen = "\\pc101338\c$\iTools\Dell-Command-Update-Application_6VFWW_WIN_5.4.0_A00.EXE"
            $Destino = "\\$RemotePC\c$\temp"

            Write-Host "Copiando recursos..." -ForegroundColor Yellow
            Copy-Item -Path $Origen -Destination $Destino

            $Origen = "\\pc101338\c$\iTools\NoSleep.exe"
            $PsExec = "C:\PSTools\PsExec.exe"  # Ruta local a PsExec

            # 1. Crear carpeta si no existe
            if (-Not (Test-Path $Destino)) {
                New-Item -ItemType Directory -Path $Destino | Out-Null
            }

            # 2. Copiar el archivo
            Write-Host "Copiando NoSleep.exe a $RemotePC..." -ForegroundColor Yellow
            Copy-Item -Path $Origen -Destination $Destino -Force

            # 3. Ejecutar NoSleep.exe en sesión interactiva (con PsExec)
            Write-Host "Ejecutando NoSleep.exe en sesión interactiva..." -ForegroundColor Green
            Start-Process $PsExec -ArgumentList "-accepteula \\$RemotePC -i -d C:\temp\NoSleep.exe"

            Invoke-Command -ComputerName $RemotePC -ScriptBlock {
            Write-Host "Validando si Dell Command está instalado..." -ForegroundColor Yellow

            $dellCommandInstalled = Get-ItemProperty -Path `
                'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*', `
                'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' `
                | Where-Object { $_.DisplayName -like "*Dell Command*Update*" }

            if ($dellCommandInstalled) {
                Write-Host "Dell Command ya está instalado." -ForegroundColor Green
            } else {
                Write-Host "Dell Command no está instalado. Instalando..." -ForegroundColor Yellow

                $installer = "C:\TEMP\Dell-Command-Update-Application_6VFWW_WIN_5.4.0_A00.EXE"
                $proc = Start-Process -FilePath $installer -ArgumentList "/s" -Wait -PassThru

                if ($proc.ExitCode -ne 0) {
                    Write-Host "❌ Instalación fallida con código $($proc.ExitCode)" -ForegroundColor Red
                    return
                } else {
                    Write-Host "✅ Instalación completada exitosamente." -ForegroundColor Green
                }
            }

            # Buscar dcu-cli
            $DCUPath = if (Test-Path "C:\Program Files (x86)\Dell\CommandUpdate\dcu-cli.exe") {
                "C:\Program Files (x86)\Dell\CommandUpdate\dcu-cli.exe"
            } elseif (Test-Path "C:\Program Files\Dell\CommandUpdate\dcu-cli.exe") {
                "C:\Program Files\Dell\CommandUpdate\dcu-cli.exe"
            } else {
                Write-Host "❌ Dell Command Update no encontrado." -ForegroundColor Red
                return
            }

            Write-Host "Ejecutando actualizaciones en segundo plano..." -ForegroundColor Yellow

            $logOut = "C:\TEMP\dcu-output.txt"
            $logErr = "C:\TEMP\dcu-error.txt"

            Start-Process -FilePath $DCUPath `
                -ArgumentList "/applyUpdates" `
                -WindowStyle Hidden `
                -RedirectStandardOutput $logOut `
                -RedirectStandardError $logErr `
                -Wait

            Write-Host "✅ Actualización finalizada. Mostrando logs..." -ForegroundColor Green

            # Mostrar logs
            Write-Host "`n--- Salida estándar (actualizaciones aplicadas): ---`n" -ForegroundColor Cyan
            Get-Content $logOut

            Write-Host "`n--- Errores (si hubo): ---`n" -ForegroundColor Magenta
            Get-Content $logErr

            # Opcional: borrar los logs después
            # Remove-Item $logOut, $logErr -Force -ErrorAction SilentlyContinue
        }

        Read-Host "Presiona ENTER para continuar"

      }
    
    6 {
            
            # 6) PROBLEMAS CON WCORP (FUNCIONA DESDE WMOBILE - TRANSPORTISTAS - WOPER - WCORP (CON DNS PEGADOS))

            if (Test-Connection -ComputerName $RemotePC -Count 2 -Quiet) {
            Write-Output "Conexión exitosa con $RemotePC."

            # Ejecutar el script en la PC remota
            Invoke-Command -ComputerName $RemotePC -ScriptBlock {
                # Acceso a Certificados Locales
                $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("My", "LocalMachine")
                $store.Open("ReadWrite")
                $currentDate = (Get-Date).AddDays(7)

                foreach ($cert in $store.Certificates) {
                    if ($cert.NotAfter -lt $currentDate -or $cert.Issuer -like "*Microsoft Intune MDM Device CA*") {
                        $store.Remove($cert)
                    }
                }
                Write-Host "Certificados eliminados y actualizados"
	
	            # Limpiar la caché de DNS
                Write-Host "Limpiando DNS"
                Clear-DnsClientCache

                Write-Host "La caché de DNS ha sido limpiada."	


                # Desconectar de cualquier red Wi-Fi conectada
                Write-Host "Desconectando de la red Wi-Fi actual..."
                netsh wlan disconnect

                # Obtener y eliminar perfiles de red Wi-Fi guardados
                $wifiProfiles = netsh wlan show profiles | Select-String "Todos los perfiles de usuario" | ForEach-Object {
                    ($_ -split ":")[1].Trim()
                }

                foreach ($profile in $wifiProfiles) {
                    Write-Host "Olvidando la red Wi-Fi: $profile"
                    netsh wlan delete profile name="$profile"
                }

                Write-Host "Desconexión y eliminación de perfiles completada."

                # Verificar y eliminar el archivo WCORP.xml si existe
                $xmlPath = "C:\Windows\temp\WCORP.xml"
                if (Test-Path $xmlPath) {
                    Remove-Item $xmlPath
                    Write-Host "El archivo $xmlPath ya existía y ha sido eliminado."
                }

                # Crear el archivo WCORP.xml con la configuración de la red Wi-Fi
                New-Item $xmlPath -ItemType File
                Set-Content $xmlPath '<?xml version="1.0"?>
                <WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
                <name>WCORP</name>
                <SSIDConfig>
                <SSID>
                <hex>57434F5250</hex>
                <name>WCORP</name>
                </SSID>
                <nonBroadcast>false</nonBroadcast>
                </SSIDConfig>
                <connectionType>ESS</connectionType>
                <connectionMode>auto</connectionMode>
                <autoSwitch>false</autoSwitch>
                <MSM>
                <security>
                <authEncryption>
                <authentication>WPA2</authentication>
                <encryption>AES</encryption>
                <useOneX>true</useOneX>
                </authEncryption>
                <OneX xmlns="http://www.microsoft.com/networking/OneX/v1">
                <authMode>machine</authMode>
                <EAPConfig><EapHostConfig xmlns="http://www.microsoft.com/provisioning/EapHostConfig">
                <EapMethod><Type xmlns="http://www.microsoft.com/provisioning/EapCommon">13</Type>
                <VendorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorId>
                <VendorType xmlns="http://www.microsoft.com/provisioning/EapCommon">0</VendorType>
                <AuthorId xmlns="http://www.microsoft.com/provisioning/EapCommon">0</AuthorId></EapMethod>
                <Config xmlns="http://www.microsoft.com/provisioning/EapHostConfig">
                <Eap xmlns="http://www.microsoft.com/provisioning/BaseEapConnectionPropertiesV1">
                <Type>13</Type>
                <EapType xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV1">
                <CredentialsSource>
                <CertificateStore>
                <SimpleCertSelection>true</SimpleCertSelection>
                </CertificateStore>
                </CredentialsSource>
                <ServerValidation>
                <DisableUserPromptForServerValidation>false</DisableUserPromptForServerValidation>
                <ServerNames></ServerNames>
                </ServerValidation>
                <DifferentUsername>false</DifferentUsername>
                <PerformServerValidation xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV2">false</PerformServerValidation>
                <AcceptServerName xmlns="http://www.microsoft.com/provisioning/EapTlsConnectionPropertiesV2">false</AcceptServerName>
                </EapType></Eap></Config></EapHostConfig></EAPConfig>
                </OneX>
                </security>
                </MSM>
                </WLANProfile>'

                # Añadir el perfil Wi-Fi desde el archivo XML
                netsh wlan add profile filename=$xmlPath user=all

                # Establecer la prioridad del perfil WCORP como la más alta
                netsh wlan set profileorder name="WCORP" interface="Wi-Fi*" priority=1

                # Conectar a la red WCORP
                netsh wlan connect name="WCORP"

                Write-Host "Conectando a la red Wi Fi..."

                # Número máximo de intentos
                $maxIntentos = 6
                $internetAccess = $false

                for ($i = 1; $i -le $maxIntentos -and -not $internetAccess; $i++) {
                    $wifiInfo = netsh wlan show interfaces
                    $wifiConnected = $wifiInfo | Select-String -Pattern "SSID\s+: WCORP"

                    if ($wifiConnected) {
                        Write-Host "Estás conectado a la red Wi-Fi WCORP."
                        $pingResult = Test-Connection -ComputerName 8.8.8.8 -Count 1 -Quiet
                        if ($pingResult) {
                            Write-Host "Tienes acceso a Internet."
                            $internetAccess = $true
                        } else {
                            Write-Host "Estás conectado a la red WCORP, pero no tienes acceso a Internet."
                            Start-Sleep -Seconds 10
                        }
                    } else {
                        Write-Host "No estás conectado a la red Wi-Fi WCORP. Intentando de nuevo..."
                        Start-Sleep -Seconds 10
                    }
                }

                if (-not $internetAccess) {
                    Write-Host "No se pudo obtener acceso a Internet después de $maxIntentos intentos."
                }

                # Actualizar directivas de grupo
                Write-Host "Actualizando directivas de grupo"
                Start-Process -FilePath "gpupdate.exe" -ArgumentList "/force" -NoNewWindow -Wait

                Write-Host "Directivas de grupo actualizadas correctamente."	


                Write-Host "PROCESO TERMINADO"
            }
        } else {
            Write-Output "No se pudo conectar con $RemotePC. El script no se ejecutará."
        }

        Read-Host "Presiona ENTER para continuar"

      }
    
    7 {
       
        Invoke-Command -ComputerName $RemotePC -ScriptBlock {

            Write-Output "Activando licencia de Windows."
            
            slmgr.vbs /ipk P9BHN-HYVGH-DVK3V-JHPJ6-HFR9M
            slmgr.vbs /ipk 3BRT8-N267D-TXT8G-W2F7F-JHW4K
            slmgr.vbs /ipk 22JFY-NPQ9G-RQ6P2-9PYM7-2R6FT

            Write-Output "Licencia aplicada."
            Read-Host "Presiona ENTER para continuar"
        }
      }
    
    8 {

        #-----------------------------------------------RECURSOS OFFICE
        $SourcePath = "\\pc101338\c$\iTools\Office"
        $SetupExe = "$SourcePath\setup.exe"
        $ConfigXml = "$SourcePath\config.xml"
        $PsExec = "C:\PSTools\PsExec.exe"  # Ruta local a PsExec
        # Ruta de destino en el equipo remoto
        $RemotePath = "\\$RemotePC\c$\Temp"

        # Copiar archivos desde pc101338 hacia el equipo remoto
        Write-Host "Copiando setup.exe y config.xml a $RemotePC..." -ForegroundColor Yellow
        try {
            Copy-Item $SetupExe -Destination $RemotePath -Force -ErrorAction Stop
            Copy-Item $ConfigXml -Destination $RemotePath -Force -ErrorAction Stop
        } catch {
            Write-Host "❌ Error al copiar archivos: $_" -ForegroundColor Red
            exit
        }

        # Validar si ya esta instalado Office
        Write-Host "Validando si office se encuentra ya instalado en $RemotePC..." -ForegroundColor Yellow

        $CheckOffice = Invoke-Command -ComputerName $RemotePC -ScriptBlock {
            Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" |
            Where-Object { $_.DisplayName -match "Microsoft 365|Office" } |
            Select-Object DisplayName, DisplayVersion
        }

        # Mostrar resultado
        if ($CheckOffice) {
            Write-Host "Office 365 esta instalado en $RemotePC. ✅" -ForegroundColor Green
            $CheckOffice | Format-Table -AutoSize
        } else {
            Write-Host "❌ No se encontró Office instalado en $RemotePC. Puede seguir instalándose o hubo un error." -ForegroundColor Red
            
            # Ejecutar instalación con PsExec
            Write-Host "Iniciando instalación silenciosa de Office 365 en $RemotePC..." -ForegroundColor Green
            Start-Process $PsExec -ArgumentList "\\$RemotePC -s -h cmd.exe /c `"C:\Temp\setup.exe /configure C:\Temp\config.xml`"" -Wait
        }

        # Esperar 5 minutos
        Write-Host "Validando instalación..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30

        # Verificar si Office fue instalado
        Write-Host "Validando instalación en $RemotePC..." -ForegroundColor Cyan
        $CheckOffice = Invoke-Command -ComputerName $RemotePC -ScriptBlock {
            Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" |
            Where-Object { $_.DisplayName -match "Microsoft 365|Office" } |
            Select-Object DisplayName, DisplayVersion
        }

        # Mostrar resultado
        if ($CheckOffice) {
            Write-Host "✅ Office 365 instalado correctamente en $RemotePC." -ForegroundColor Green
            $CheckOffice | Format-Table -AutoSize
        } else {
            Write-Host "❌ No se encontró Office instalado en $RemotePC. Puede seguir instalándose o hubo un error." -ForegroundColor Red
        }

        Read-Host "Presiona ENTER para continuar"                      
      }
    
    9 {
            Write-Host "1)Lexmark"
            Write-Host "2)Zebra WIFI"
            $opcion = Read-Host "Ingrese una opcion"

            if($opcion -eq 1){
                Write-Host "Copiando driver..." -ForegroundColor Yellow
                Copy-Item -Path "\\pc101338\c$\iTools\Drivers-IMs\Lexmark\lmud1n40.inf" -Destination "\\$RemotePC\c$\" -Force
                Write-Host "Copiado" -ForegroundColor green

                Invoke-Command -ComputerName $RemotePC -ScriptBlock {
                    Try {
                        $printerName = Read-Host "Ingresa el nombre de la impresora"
                        $ipAddress = Read-Host "Ingresa la dirección IP de la impresora"

                        # Verificar si el archivo INF existe
                        if (-Not (Test-Path "C:\lmud1n40.inf")) {
                            Write-Host "❌ Error: El archivo C:\lmud1n40.inf no se encuentra." -ForegroundColor red
                            exit
                        }

                        # Intentar instalar el controlador
                        Write-Host "Instalando el controlador de la impresora..." -ForegroundColor yellow
                        Try {
                            pnputil /add-driver "C:\lmud1n40.inf" /install
                            Write-Host "✅ Controlador instalado correctamente." -ForegroundColor green
                        } Catch {
                            Write-Host "❌ Error al instalar el controlador: $_" -ForegroundColor red
                            exit
                        }

                        Start-Sleep -Seconds 5

                        # Verificar si el controlador fue registrado
                        if (-Not (Get-PrinterDriver | Where-Object { $_.Name -eq "Lexmark Universal v2 PS3" })) {
                            Write-Host "❌ Error: El controlador no está registrado. Intentando agregarlo..." -ForegroundColor yellow
                            Add-PrinterDriver -Name "Lexmark Universal v2 PS3"
                        }

                        Write-Host "Registrando el controlador en Windows..." -ForegroundColor yellow
                        rundll32 printui.dll,PrintUIEntry /ia /m "Lexmark Universal v2 PS3" /f "C:\lmud1n40.inf"

                        Start-Sleep -Seconds 5

                        # Crear puerto si no existe
                        if (-Not (Get-PrinterPort | Where-Object { $_.Name -eq $ipAddress })) {
                            Write-Host "Creando el puerto TCP/IP $ipAddress..."
                            Add-PrinterPort -Name $ipAddress -PrinterHostAddress $ipAddress
                        }

                        # Agregar la impresora
                        Write-Host "Agregando la impresora con el nombre: $printerName..." -ForegroundColor yellow
                        Try {
                            Add-Printer -Name $printerName -DriverName "Lexmark Universal v2 PS3" -PortName $ipAddress
                            Write-Host "✅ Impresora '$printerName' instalada correctamente en IP $ipAddress" -ForegroundColor green
                        } Catch {
                            Write-Host "❌ Error al agregar la impresora: $_" -ForegroundColor red
                        }

                    } Catch {
                        Write-Host "❌ Se produjo un error inesperado: $_" -ForegroundColor red
                        exit
                    }
                }

                Write-Host "🎉 Instalación finalizada!" -ForegroundColor green

            }

            if($opcion -eq 2){
                Write-Host "Copiando driver..." -ForegroundColor Yellow
                Copy-Item -Path "\\pc101338\c$\iTools\Drivers-IMs\Zebras\ZBRN.inf" -Destination "\\$RemotePC\c$\" -Force
                Write-Host "Copiado" -ForegroundColor green

                Invoke-Command -ComputerName $RemotePC -ScriptBlock {
                    Try {
                        $printerName = Read-Host "Ingresa el nombre de la impresora"
                        $ipAddress = Read-Host "Ingresa la dirección IP de la impresora"

                        # Verificar si el archivo INF existe
                        if (-Not (Test-Path "C:\ZBRN.inf")) {
                            Write-Host "❌ Error: El archivo C:\ZBRN.inf no se encuentra." -ForegroundColor red
                            exit
                        }

                        # Intentar instalar el controlador
                        Write-Host "Instalando el controlador de la impresora..." -ForegroundColor yellow
                        Try {
                            pnputil /add-driver "C:\ZBRN.inf" /install
                            Write-Host "✅ Controlador instalado correctamente." -ForegroundColor green
                        } Catch {
                            Write-Host "❌ Error al instalar el controlador: $_" -ForegroundColor red
                            exit
                        }

                        Start-Sleep -Seconds 5

                        # Verificar si el controlador fue registrado
                        if (-Not (Get-PrinterDriver | Where-Object { $_.Name -eq "ZDesigner ZD420-203dpi ZPL" })) {
                            Write-Host "❌ Error: El controlador no está registrado. Intentando agregarlo..." -ForegroundColor yellow
                            Add-PrinterDriver -Name "ZDesigner ZD420-203dpi ZPL"
                        }

                        Write-Host "Registrando el controlador en Windows..." -ForegroundColor yellow
                        rundll32 printui.dll,PrintUIEntry /ia /m "ZDesigner ZD420-203dpi ZPL" /f "C:\ZBRN.inf"

                        Start-Sleep -Seconds 5

                        # Crear puerto si no existe
                        if (-Not (Get-PrinterPort | Where-Object { $_.Name -eq $ipAddress })) {
                            Write-Host "Creando el puerto TCP/IP $ipAddress..."
                            Add-PrinterPort -Name $ipAddress -PrinterHostAddress $ipAddress
                        }

                        # Agregar la impresora
                        Write-Host "Agregando la impresora con el nombre: $printerName..." -ForegroundColor yellow
                        Try {
                            Add-Printer -Name $printerName -DriverName "ZDesigner ZD420-203dpi ZPL" -PortName $ipAddress
                            Write-Host "✅ Impresora '$printerName' instalada correctamente en IP $ipAddress" -ForegroundColor green
                        } Catch {
                            Write-Host "❌ Error al agregar la impresora: $_" -ForegroundColor red
                        }

                    } Catch {
                        Write-Host "❌ Se produjo un error inesperado: $_" -ForegroundColor red
                        exit
                    }
                }

                Write-Host "🎉 Instalación finalizada!" -ForegroundColor green
            }

            Read-Host "Presiona ENTER para continuar"
        }

        10 {
            # Solicitar la IP de la impresora al usuario
            $ip = Read-Host "Ingrese la IP de la impresora Zebra"
            $port = 9100  # Puerto RAW por defecto

            # Comando ZPL de calibración (solo calibración de medios)
            $zpl = "~JC`r`n"

            try {
                # Conectar por TCP
                $client = New-Object System.Net.Sockets.TcpClient($ip, $port)
                $stream = $client.GetStream()
                $writer = New-Object System.IO.StreamWriter($stream)
    
                # Enviar comando
                $writer.Write($zpl)
                $writer.Flush()
    
                Write-Host "✅ Calibración enviada correctamente a la Zebra en $ip"
    
                # Cerrar conexiones
                $writer.Close()
                $client.Close()
            }
            catch {
                Write-Host "❌ Error al conectar con la impresora en $ip : $_"
            }
        }

        11 {
            $RemoteScript = {
                function Get-InstalledApplications {
                    param ([string]$RegistryPath)

                    Get-ItemProperty -Path $RegistryPath -ErrorAction SilentlyContinue | ForEach-Object {
                        $_ | Select-Object @{
                            Name       = 'Name'
                            Expression = { $_.DisplayName }
                        }, @{
                            Name       = 'Version'
                            Expression = { $_.DisplayVersion }
                        }, @{
                            Name       = 'Publisher'
                            Expression = { $_.Publisher }
                        }, @{
                            Name       = 'UninstallString'
                            Expression = { $_.UninstallString }
                        }
                    } | Where-Object { $_.Name -ne $null }
                }

                $RegistryPaths = @(
                    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
                    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
                )

                # Obtener todas las apps
                $Applications = foreach ($Path in $RegistryPaths) {
                    Get-InstalledApplications -RegistryPath $Path
                }

                # Ordenar
                $Applications = $Applications | Sort-Object Name

                # Mostrar con índice numérico
                $IndexedApps = $Applications | Select-Object @{Name='Index';Expression={[array]::IndexOf($Applications, $_)}}, Name, Version, Publisher
                $IndexedApps | Format-Table -AutoSize

                # Selección del usuario
                $Choice = Read-Host "Ingrese el número de la aplicación a desinstalar (o ENTER para no desinstalar)"

                if (-not $Choice) {
                    Write-Host "`nNo se desinstaló ninguna aplicación."
                    return
                }

                if ($Choice -notmatch '^\d+$' -or $Choice -ge $Applications.Count) {
                    Write-Host "`nNúmero inválido."
                    return
                }

                $SelectedApp = $Applications[$Choice]

                Write-Host "`nDesinstalando: $($SelectedApp.Name)"

                $UninstallCmd = $SelectedApp.UninstallString

                if (-not $UninstallCmd) {
                    Write-Host "No se encontró un comando de desinstalación para esta aplicación."
                    return
                }

                # Si requiere cmd /c
                if ($UninstallCmd -like "msiexec*") {
                    Start-Process "cmd.exe" "/c $UninstallCmd /quiet /norestart" -Wait
                } else {
                    Start-Process "cmd.exe" "/c `"$UninstallCmd`"" -Wait
                }

                Write-Host "`nProceso finalizado."
            }

            # Ejecutar remoto
            Invoke-Command -ComputerName $RemotePC -ScriptBlock $RemoteScript

            Read-Host "Presiona ENTER para continuar"
        }



        0 {
            $bandera = $false

            while ($bandera -eq $false){
            # Verificar la conexión al equipo remoto
                $RemotePC = Read-Host "Inventario"
                if (Test-Connection -ComputerName $RemotePC -Count 2 -Quiet) {
                    Write-Host "Conexión exitosa con $RemotePC."
                    $bandera = $true

                    try {
                        Write-Host "Estableciendo ExecutionPolicy en $RemotePC..." -ForegroundColor Cyan

                        $cmd1 = psexec \\$RemotePC powershell -Command "Set-ExecutionPolicy RemoteSigned -Force"
                        $cmd2 = psexec \\$RemotePC powershell -Command "Set-ExecutionPolicy RemoteSigned -Force"

                        Write-Host "ExecutionPolicy actualizado correctamente en $RemotePC" -ForegroundColor Green
                    }
                    catch {
                        Write-Host "Error al actualizar ExecutionPolicy en $RemotePC" -ForegroundColor Red
                        Write-Host "Detalles: $($_.Exception.Message)" -ForegroundColor Yellow
                    }


                    # Verificar si la carpeta Temp existe en el equipo remoto
                        Invoke-Command -ComputerName $RemotePC -ScriptBlock {
                            $folder = "C:\TEMP"
                            if (!(Test-Path $folder)) {
                                New-Item -Path $folder -ItemType Directory -Force
                            }
                        }
                } else {
                    Write-Host "No se pudo conectar con $RemotePC. Verifique la conexión."
                    $RemotePC = Read-Host "Inventario"
                    Read-Host "Presiona ENTER para continuar"
                }
            }
        }
     
}

cls

} 