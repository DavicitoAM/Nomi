# Optional fallback for Windows when PostgreSQL 18 is installed and Docker is unavailable.
# Own cluster under this workspace; does not touch the installed PostgreSQL service.
$ErrorActionPreference = 'Stop'
$nomiRoot = Split-Path -Parent $PSScriptRoot
$nomiPg = 'C:\Program Files\PostgreSQL\18\bin'
$nomiData = Join-Path $nomiRoot '.local\postgres'
if (-not (Test-Path -LiteralPath (Join-Path $nomiPg 'initdb.exe'))) { throw 'Instala PostgreSQL 18 o usa docker compose up -d.' }
New-Item -ItemType Directory -Force -Path (Join-Path $nomiRoot '.local') | Out-Null
if (-not (Test-Path -LiteralPath (Join-Path $nomiData 'PG_VERSION'))) {
    & (Join-Path $nomiPg 'initdb.exe') -D $nomiData -U nomi --auth=trust --encoding=UTF8 --locale=C
    if ($LASTEXITCODE -ne 0) { throw 'Falló initdb.' }
}
& (Join-Path $nomiPg 'pg_ctl.exe') -D $nomiData status
if ($LASTEXITCODE -ne 0) {
    & (Join-Path $nomiPg 'pg_ctl.exe') -D $nomiData -l (Join-Path $nomiRoot '.local\postgres.log') -o '-p 54329 -h 127.0.0.1 -c log_error_verbosity=terse -c log_min_error_statement=panic' start
    if ($LASTEXITCODE -ne 0) { throw 'Falló el arranque de PostgreSQL.' }
}
foreach ($nomiDb in @('nomi','nomi_test')) {
    $nomiExists = & (Join-Path $nomiPg 'psql.exe') -h 127.0.0.1 -p 54329 -U nomi -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$nomiDb'"
    if ($nomiExists -ne '1') {
        & (Join-Path $nomiPg 'createdb.exe') -h 127.0.0.1 -p 54329 -U nomi $nomiDb
        if ($LASTEXITCODE -ne 0) { throw "No se pudo crear $nomiDb." }
    }
}
Write-Host 'PostgreSQL local listo en 127.0.0.1:54329. Sólo desarrollo: autenticación trust en loopback.'
