# Run from PowerShell: .\scripts\dev.ps1
$ErrorActionPreference = 'Stop'
$nomiRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $nomiRoot
$nomiPython = Join-Path $nomiRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $nomiPython)) { throw 'Primero instala las dependencias: consulta README.md.' }
New-Item -ItemType Directory -Force -Path (Join-Path $nomiRoot '.local') | Out-Null
& $nomiPython -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'No se pudo migrar PostgreSQL. Revisa DATABASE_URL y que la base esté iniciada.' }
$nomiApi = Start-Process -FilePath $nomiPython -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000','--no-access-log') -WorkingDirectory $nomiRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $nomiRoot '.local\api.log') -RedirectStandardError (Join-Path $nomiRoot '.local\api-error.log')
$nomiWorker = Start-Process -FilePath $nomiPython -ArgumentList @('-m','app.worker') -WorkingDirectory $nomiRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $nomiRoot '.local\worker.log') -RedirectStandardError (Join-Path $nomiRoot '.local\worker-error.log')
$nomiMailbox = Start-Process -FilePath $nomiPython -ArgumentList @('-m','app.mailbox') -WorkingDirectory $nomiRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $nomiRoot '.local\mailbox.log') -RedirectStandardError (Join-Path $nomiRoot '.local\mailbox-error.log')
try {
    Write-Host 'Nomi: http://localhost:3000 | API: http://127.0.0.1:8000/docs'
    Write-Host 'Buzón local: http://localhost:8025 | Correos de prueba, sin envío externo'
    npm.cmd run dev
} finally {
    if (-not $nomiApi.HasExited) { Stop-Process -Id $nomiApi.Id }
    if (-not $nomiWorker.HasExited) { Stop-Process -Id $nomiWorker.Id }
    if (-not $nomiMailbox.HasExited) { Stop-Process -Id $nomiMailbox.Id }
}
