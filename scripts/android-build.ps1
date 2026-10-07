param([switch]$Release)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'android-env.ps1')
Push-Location -LiteralPath $nomiRoot
try {
    npm.cmd run mobile:sync
    if ($LASTEXITCODE -ne 0) { throw 'Falló el build/sync móvil.' }
    Push-Location -LiteralPath (Join-Path $nomiRoot 'apps/mobile/android')
    try {
        $nomiTask = if ($Release) { ':app:bundleRelease' } else { ':app:assembleDebug' }
        & .\gradlew.bat $nomiTask :app:testDebugUnitTest :app:lintDebug --no-daemon --no-watch-fs --max-workers=2 --console plain
        if ($LASTEXITCODE -ne 0) { throw 'Falló el build Android.' }
    } finally { Pop-Location }
} finally { Pop-Location }
