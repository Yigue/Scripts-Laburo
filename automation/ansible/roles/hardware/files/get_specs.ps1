# Helper function to parse WMI dates safely
function Convert-WmiDate {
    param([object]$InputDate)
    
    if ($null -eq $InputDate) { return $null }
    
    try {
        if ($InputDate -is [DateTime]) { return $InputDate }
        if ($InputDate -is [string]) {
            return [DateTime]::ParseExact($InputDate.Split('.')[0], "yyyyMMddHHmmss", $null)
        }
    } catch {
        Write-Verbose "Error parsing date: $_"
    }
    return $null
}

$ErrorActionPreference = 'SilentlyContinue'

# 1. Get OS Info for Dates
$os = Get-CimInstance -ClassName Win32_OperatingSystem
$installDate = Convert-WmiDate $os.InstallDate
$lastBoot = Convert-WmiDate $os.LastBootUpTime

# Get Windows Display Version (e.g. 22H2)
try {
    $displayVersion = Get-ItemPropertyValue -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' -Name DisplayVersion -ErrorAction Stop
} catch {
    $displayVersion = "N/A"
}


# 2. Get Patch Info (RollupFix)
$patchPath = "Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\Packages"
$latestPatch = Get-ChildItem -Path "$patchPath\Package_for_RollupFix*" -ErrorAction SilentlyContinue | 
    Sort-Object PSChildName -Descending | 
    Select-Object -First 1 | 
    ForEach-Object { $_.PSChildName -replace ".*~", "" }

# 3. Get Network Info (Optimized)
# Filter out virtual adapters commonly used by VPNs or Virtualization, unless they are the only ones
$adapters = Get-CimInstance -ClassName Win32_NetworkAdapterConfiguration -Filter "IPEnabled = TRUE" | 
    Where-Object { $_.Description -notmatch "VMware|Virtual|VPN|Loopback|Pseudo" } |
    Select-Object Description, IPAddress, MACAddress

# 4. Construct Output Object
$output = [ordered]@{
    DisplayVersion = $displayVersion
    InstallDate = if ($installDate) { $installDate.ToString("dd/MM/yyyy HH:mm:ss") } else { "N/A" }
    LastBoot    = if ($lastBoot) { $lastBoot.ToString("dd/MM/yyyy HH:mm:ss") } else { "N/A" }
    LatestPatch = if ($latestPatch) { $latestPatch } else { "N/A" }
    Adapters    = $adapters
}

$output | ConvertTo-Json -Depth 2
