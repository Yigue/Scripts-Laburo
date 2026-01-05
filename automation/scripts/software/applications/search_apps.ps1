# Busca aplicaciones por nombre
# Parámetro: $SearchTerm - Término de búsqueda

param(
    [Parameter(Mandatory=$true)]
    [string]$SearchTerm
)

try {
    # Importar lista de aplicaciones
    if (!(Test-Path "C:\TEMP\apps_list.xml")) {
        Write-Output "❌ No se encontró lista de aplicaciones"
        Write-Output "   Ejecutar primero 'Listar aplicaciones'"
        throw "Lista de aplicaciones no encontrada"
    }

    $apps = Import-Clixml -Path "C:\TEMP\apps_list.xml"

    # Buscar aplicaciones que coincidan
    $results = @()
    $index = 0
    foreach ($app in $apps) {
        if ($app.Name -like "*$SearchTerm*") {
            $results += [PSCustomObject]@{
                Index = $index
                Name = $app.Name
                Version = $app.Version
                Publisher = $app.Publisher
            }
        }
        $index++
    }

    if ($results.Count -eq 0) {
        Write-Output "🔍 No se encontraron aplicaciones con: '$SearchTerm'"
    }
    else {
        Write-Output "🔍 Resultados de búsqueda para: '$SearchTerm'"
        Write-Output ""
        $results | Format-Table Index, Name, Version, Publisher -AutoSize
        Write-Output ""
        Write-Output "✅ Encontradas: $($results.Count) aplicaciones"
    }

} catch {
    Write-Output "❌ ERROR: $($_.Exception.Message)"
    Write-Output "StackTrace: $($_.ScriptStackTrace)"
    throw
}

