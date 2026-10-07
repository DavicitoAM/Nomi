# Local toolchain only. Does not change machine/user environment variables.
$nomiRoot = Split-Path -Parent $PSScriptRoot
$nomiJdkRoot = Join-Path $nomiRoot '.local/android-toolchain/jdk'
if (Test-Path -LiteralPath $nomiJdkRoot) {
    $env:JAVA_HOME = (Get-ChildItem -LiteralPath $nomiJdkRoot -Directory | Select-Object -First 1).FullName
}
if (Test-Path -LiteralPath (Join-Path $nomiRoot '.local/android-sdk')) {
    $env:ANDROID_HOME = Join-Path $nomiRoot '.local/android-sdk'
}
$env:GRADLE_USER_HOME = Join-Path $nomiRoot '.local/gradle'
$nomiTemp = Join-Path $nomiRoot '.local/java-tmp'
New-Item -ItemType Directory -Force -Path $nomiTemp | Out-Null
$env:JAVA_TOOL_OPTIONS = "-Djdk.net.unixdomain.tmpdir=$nomiTemp -Djava.io.tmpdir=$nomiTemp"
