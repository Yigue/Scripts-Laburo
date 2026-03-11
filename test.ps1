<#
.SYNOPSIS
  SCCM Connectivity + Query Diagnostic (WinRM / WMI-DCOM / ConfigMgr module / SQL) and optional device lookup.

.DESCRIPTION
  - Tests network reachability (DNS, Ping, key ports).
  - Attempts:
      1) WinRM (WSMan) reachability + CIM over WSMan
      2) WMI/CIM over DCOM (requires creds if not already allowed)
      3) ConfigMgr Console module cmdlets (Get-CMDevice) if installed
      4) SQL query (if -SqlServer/-SqlDatabase provided)
  - Produces a result object and recommends the best method that actually works from *your* machine.

.EXAMPLE
  .\Sccm-Diag.ps1 -SccmServer MSCOCSRV.andreani.com.ar -SiteCode PRI -DeviceName NB100147

.EXAMPLE
  .\Sccm-Diag.ps1 -SccmServer MSCOCSRV.andreani.com.ar -SiteCode PRI -DeviceName NB100147 -SqlServer SQLCM01 -SqlDatabase CM_PRI -UseIntegratedSecurity
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [string]$SccmServer,

  [Parameter(Mandatory=$true)]
  [string]$SiteCode,

  [Parameter(Mandatory=$true)]
  [string]$DeviceName,

  # Optional: SQL method
  [string]$SqlServer,
  [string]$SqlDatabase,
  [switch]$UseIntegratedSecurity,
  [string]$SqlUser,
  [string]$SqlPassword,

  # Optional: if you want to prompt for creds to try DCOM / WinRM explicitly
  [switch]$PromptForCredential
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-Port {
  param([string]$HostName, [int]$Port)
  try {
    $r = Test-NetConnection -ComputerName $HostName -Port $Port -WarningAction SilentlyContinue
    return [pscustomobject]@{
      Port = $Port
      TcpTestSucceeded = [bool]$r.TcpTestSucceeded
      RemoteAddress = $r.RemoteAddress
    }
  } catch {
    return [pscustomobject]@{
      Port = $Port
      TcpTestSucceeded = $false
      Error = $_.Exception.Message
    }
  }
}

function Try-WinRM {
  param([string]$HostName, [pscredential]$Cred)

  $out = [ordered]@{
    Reachable5985 = $false
    Reachable5986 = $false
    WsManOK = $false
    CimRootSmsOK = $false
    Error = $null
  }

  $p5985 = Test-Port -HostName $HostName -Port 5985
  $p5986 = Test-Port -HostName $HostName -Port 5986
  $out.Reachable5985 = $p5985.TcpTestSucceeded
  $out.Reachable5986 = $p5986.TcpTestSucceeded

  if (-not ($out.Reachable5985 -or $out.Reachable5986)) {
    $out.Error = "WinRM no accesible (5985/5986 cerrados desde este host)."
    return [pscustomobject]$out
  }

  try {
    if ($Cred) { Test-WSMan -ComputerName $HostName -Credential $Cred | Out-Null }
    else { Test-WSMan -ComputerName $HostName | Out-Null }
    $out.WsManOK = $true
  } catch {
    $out.Error = "Test-WSMan falló: $($_.Exception.Message)"
    return [pscustomobject]$out
  }

  # Try a cheap CIM call over WSMan (WinRM) to SCCM Provider root\SMS
  try {
    if ($Cred) {
      Get-CimInstance -ComputerName $HostName -Namespace "root\SMS" -ClassName "SMS_ProviderLocation" -Credential $Cred -ErrorAction Stop | Out-Null
    } else {
      Get-CimInstance -ComputerName $HostName -Namespace "root\SMS" -ClassName "SMS_ProviderLocation" -ErrorAction Stop | Out-Null
    }
    $out.CimRootSmsOK = $true
  } catch {
    $out.Error = "CIM por WinRM llegó pero no pudo consultar root\SMS: $($_.Exception.Message)"
  }

  return [pscustomobject]$out
}

function Try-DCOM {
  param([string]$HostName, [pscredential]$Cred)

  $out = [ordered]@{
    Rpc135Open = $false
    DcomCimSessionOK = $false
    ProviderRootSmsOK = $false
    Error = $null
  }

  $p135 = Test-Port -HostName $HostName -Port 135
  $out.Rpc135Open = $p135.TcpTestSucceeded
  if (-not $out.Rpc135Open) {
    $out.Error = "RPC 135 cerrado; DCOM/WMI remoto no viable."
    return [pscustomobject]$out
  }

  try {
    $so = New-CimSessionOption -Protocol Dcom
    if ($Cred) { $s = New-CimSession -ComputerName $HostName -SessionOption $so -Credential $Cred }
    else { $s = New-CimSession -ComputerName $HostName -SessionOption $so }
    $out.DcomCimSessionOK = $true

    Get-CimInstance -CimSession $s -Namespace "root\SMS" -ClassName "SMS_ProviderLocation" -ErrorAction Stop | Out-Null
    $out.ProviderRootSmsOK = $true
    $s | Remove-CimSession
  } catch {
    $out.Error = $_.Exception.Message
  }

  return [pscustomobject]$out
}

function Try-ConfigMgrModule {
  param([string]$Site, [string]$Device)

  $out = [ordered]@{
    ModulePresent = $false
    Imported = $false
    SiteDriveFound = $false
    QueryOK = $false
    DeviceResult = $null
    Error = $null
  }

  try {
    $psd1 = Join-Path $env:SMS_ADMIN_UI_PATH "..\ConfigurationManager.psd1"
    if (Test-Path $psd1) {
      $out.ModulePresent = $true
      Import-Module $psd1 -ErrorAction Stop
      $out.Imported = $true
    } else {
      $out.Error = "No se encontró ConfigurationManager.psd1 (consola no instalada)."
      return [pscustomobject]$out
    }

    $drives = Get-PSDrive -PSProvider CMSite -ErrorAction Stop
    $drive = $drives | Where-Object { $_.Name -ieq $Site } | Select-Object -First 1
    if (-not $drive) {
      # take first CMSite drive if SiteCode mismatch
      $drive = $drives | Select-Object -First 1
    }
    if ($drive) {
      $out.SiteDriveFound = $true
      Set-Location ("{0}:" -f $drive.Name)

      # Minimal fields (avoid huge objects)
      $dev = Get-CMDevice -Name $Device -ErrorAction Stop |
        Select-Object Name, ResourceId, ClientType, IsClient, LastActiveTime, LastLogonUserName

      $out.DeviceResult = $dev
      $out.QueryOK = $true
    } else {
      $out.Error = "No se encontró drive CMSite. La consola puede no estar conectando al sitio o RBAC limita."
    }

  } catch {
    $out.Error = $_.Exception.Message
  } finally {
    try { Set-Location $PSScriptRoot } catch {}
  }

  return [pscustomobject]$out
}

function Invoke-SqlQuery {
  param(
    [string]$Server,
    [string]$Database,
    [string]$Query,
    [switch]$IntegratedSecurity,
    [string]$User,
    [string]$Pass
  )

  $csb = New-Object System.Data.SqlClient.SqlConnectionStringBuilder
  $csb.DataSource = $Server
  $csb.InitialCatalog = $Database
  if ($IntegratedSecurity) {
    $csb.IntegratedSecurity = $true
  } else {
    $csb.UserID = $User
    $csb.Password = $Pass
  }
  $csb.ConnectTimeout = 5

  $conn = New-Object System.Data.SqlClient.SqlConnection $csb.ConnectionString
  $cmd  = $conn.CreateCommand()
  $cmd.CommandTimeout = 10
  $cmd.CommandText = $Query

  $dt = New-Object System.Data.DataTable
  $conn.Open()
  try {
    $r = $cmd.ExecuteReader()
    $dt.Load($r)
  } finally {
    $conn.Close()
  }
  return $dt
}

function Try-SqlMethod {
  param(
    [string]$Server,
    [string]$Database,
    [string]$Device,
    [switch]$IntegratedSecurity,
    [string]$User,
    [string]$Pass
  )

  $out = [ordered]@{
    Provided = $false
    Port1433Open = $false
    QueryOK = $false
    DeviceResult = $null
    Error = $null
  }

  if (-not $Server -or -not $Database) {
    $out.Error = "SQL no configurado: faltan -SqlServer y/o -SqlDatabase."
    return [pscustomobject]$out
  }

  $out.Provided = $true
  $p1433 = Test-Port -HostName $Server -Port 1433
  $out.Port1433Open = $p1433.TcpTestSucceeded
  if (-not $out.Port1433Open) {
    $out.Error = "Puerto 1433 cerrado hacia $Server (o SQL usa otro puerto/instancia)."
    return [pscustomobject]$out
  }

  try {
    # Minimal, commonly available view
    $q = @"
SELECT TOP 1
  sys.Name0      AS Name,
  sys.ResourceID AS ResourceId,
  sys.Client0    AS Client,
  sys.Active0    AS Active
FROM v_R_System sys
WHERE sys.Name0 = '$Device';
"@

    $dt = Invoke-SqlQuery -Server $Server -Database $Database -Query $q -IntegratedSecurity:$IntegratedSecurity -User $User -Pass $Pass
    $out.DeviceResult = $dt
    $out.QueryOK = $true
  } catch {
    $out.Error = $_.Exception.Message
  }

  return [pscustomobject]$out
}

# ---------- Main ----------
$cred = $null
if ($PromptForCredential) {
  $cred = Get-Credential -Message "Credencial para probar acceso remoto (WinRM/DCOM) a $SccmServer"
}

$result = [ordered]@{
  Input = [pscustomobject]@{ SccmServer=$SccmServer; SiteCode=$SiteCode; DeviceName=$DeviceName; SqlServer=$SqlServer; SqlDatabase=$SqlDatabase }
  Dns = $null
  Ping = $null
  Ports = @()
  WinRM = $null
  DCOM = $null
  ConfigMgrModule = $null
  Sql = $null
  RecommendedMethod = $null
  DeviceInventory = $null
}

# DNS + ping
try {
  $dns = Resolve-DnsName $SccmServer -ErrorAction Stop | Select-Object -First 1 Name, IPAddress
  $result.Dns = $dns
} catch {
  $result.Dns = [pscustomobject]@{ Error = $_.Exception.Message }
}

try {
  $p = Test-NetConnection -ComputerName $SccmServer -WarningAction SilentlyContinue
  $result.Ping = [pscustomobject]@{
    PingSucceeded = [bool]$p.PingSucceeded
    RemoteAddress = $p.RemoteAddress
    SourceAddress = $p.SourceAddress
    InterfaceAlias = $p.InterfaceAlias
  }
} catch {
  $result.Ping = [pscustomobject]@{ Error = $_.Exception.Message }
}

# Common ports to test (SCCM-ish + remoting + SQL)
$portsToTest = @(135, 445, 5985, 5986, 80, 443, 1433)
foreach ($pt in $portsToTest) {
  $result.Ports += (Test-Port -HostName $SccmServer -Port $pt)
}

# Attempt methods
$result.WinRM = Try-WinRM -HostName $SccmServer -Cred $cred
$result.DCOM  = Try-DCOM  -HostName $SccmServer -Cred $cred
$result.ConfigMgrModule = Try-ConfigMgrModule -Site $SiteCode -Device $DeviceName
$result.Sql = Try-SqlMethod -Server $SqlServer -Database $SqlDatabase -Device $DeviceName -IntegratedSecurity:$UseIntegratedSecurity -User $SqlUser -Pass $SqlPassword

# Recommendation logic (pick best viable)
# Priority: ConfigMgr cmdlets > DCOM Provider > WinRM Provider > SQL (if configured)
if ($result.ConfigMgrModule.QueryOK) {
  $result.RecommendedMethod = "ConfigMgrModule (Get-CMDevice)"
  $result.DeviceInventory = $result.ConfigMgrModule.DeviceResult
}
elseif ($result.DCOM.ProviderRootSmsOK) {
  $result.RecommendedMethod = "WMI/DCOM to SMS Provider (root\\SMS / root\\SMS\\site_$SiteCode)"
  # If DCOM works, try actual inventory query
  try {
    $so = New-CimSessionOption -Protocol Dcom
    $sess = if ($cred) { New-CimSession -ComputerName $SccmServer -SessionOption $so -Credential $cred } else { New-CimSession -ComputerName $SccmServer -SessionOption $so }
    $ns = "root\sms\site_$SiteCode"
    $q  = "SELECT Name, ResourceId, Client, Active, LastLogonUserName, OperatingSystemNameandVersion FROM SMS_R_System WHERE Name = '$DeviceName'"
    $dev = Get-CimInstance -CimSession $sess -Namespace $ns -Query $q -ErrorAction Stop
    $result.DeviceInventory = $dev
    $sess | Remove-CimSession
  } catch {
    $result.DeviceInventory = [pscustomobject]@{ Error = $_.Exception.Message; Note="DCOM ok pero query site namespace falló (permisos/RBAC/SiteCode)." }
  }
}
elseif ($result.WinRM.CimRootSmsOK) {
  $result.RecommendedMethod = "CIM over WinRM (WSMan) to SMS Provider"
  try {
    $ns = "root\sms\site_$SiteCode"
    $q  = "SELECT Name, ResourceId, Client, Active, LastLogonUserName, OperatingSystemNameandVersion FROM SMS_R_System WHERE Name = '$DeviceName'"
    $dev = if ($cred) {
      Get-CimInstance -ComputerName $SccmServer -Namespace $ns -Query $q -Credential $cred -ErrorAction Stop
    } else {
      Get-CimInstance -ComputerName $SccmServer -Namespace $ns -Query $q -ErrorAction Stop
    }
    $result.DeviceInventory = $dev
  } catch {
    $result.DeviceInventory = [pscustomobject]@{ Error = $_.Exception.Message }
  }
}
elseif ($result.Sql.QueryOK) {
  $result.RecommendedMethod = "SQL views (v_R_System)"
  $result.DeviceInventory = $result.Sql.DeviceResult
}
else {
  $result.RecommendedMethod = "Ninguno viable desde este host (revisar puertos/permisos o usar jumpbox/SQL)."
}

# Output: pretty + JSON copy
"================ SCCM DIAG SUMMARY ================"
$result | ConvertTo-Json -Depth 6
"=================================================="
