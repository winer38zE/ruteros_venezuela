# Instala la app en el telefono conectado por USB (modo debug).
# Uso: clic derecho -> Ejecutar con PowerShell, o desde mobile:
#   powershell -ExecutionPolicy Bypass -File .\instalar_en_telefono.ps1

$ErrorActionPreference = "Stop"

$jbr = "C:\Program Files\Android\Android Studio\jbr"
if (Test-Path $jbr) {
    $env:JAVA_HOME = $jbr
    $env:Path = "$jbr\bin;$env:Path"
}

$sdk = Join-Path $env:LOCALAPPDATA "Android\sdk"
if (Test-Path $sdk) {
    $env:ANDROID_HOME = $sdk
    $env:ANDROID_SDK_ROOT = $sdk
    $platformTools = Join-Path $sdk "platform-tools"
    if (Test-Path $platformTools) {
        $env:Path = "$platformTools;$env:Path"
    }
}

Set-Location $PSScriptRoot

Write-Host "Dispositivos detectados:"
flutter devices

Write-Host ""
Write-Host "Compilando APK debug e instalando en el telefono Android..."
flutter build apk --debug
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

flutter install --debug -d android
if ($LASTEXITCODE -ne 0) {
    $apk = Join-Path $PSScriptRoot "build\app\outputs\flutter-apk\app-debug.apk"
    if (-not (Test-Path $apk)) {
        Write-Error "No se encontro $apk"
    }
    Write-Host "flutter install fallo; usando adb directo..."
    & adb install -r $apk
}

Write-Host "Listo."
