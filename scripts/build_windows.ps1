$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$PythonCommand = Get-Command python -ErrorAction SilentlyContinue
$InstalledPython = Get-ChildItem "$env:LOCALAPPDATA\Python\pythoncore-*\python.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
$PythonExe = if ($PythonCommand) {
    $PythonCommand.Source
} elseif ($InstalledPython) {
    $InstalledPython.FullName
} elseif (Test-Path "$env:LOCALAPPDATA\Python\bin\python.exe") {
    "$env:LOCALAPPDATA\Python\bin\python.exe"
} else {
    throw "Python을 찾을 수 없습니다. Python 3.11 이상을 설치한 뒤 다시 실행해 주세요."
}

$BuildPython = ".venv\Scripts\python.exe"
if (-not (Test-Path $BuildPython)) { & $PythonExe -m venv .venv }
$UseTargetPackages = $false
try { & $BuildPython --version | Out-Null; if ($LASTEXITCODE -ne 0) { throw "venv launcher failed" } } catch { $UseTargetPackages = $true }

if ($UseTargetPackages) {
    $PackageDir = Join-Path $ProjectRoot ".build-packages"
    & $PythonExe -m pip install --upgrade --target $PackageDir -r requirements.txt
    $env:PYTHONPATH = $PackageDir
    $Runner = $PythonExe
} else {
    & $BuildPython -m pip install --upgrade pip
    & $BuildPython -m pip install -r requirements.txt
    $Runner = $BuildPython
}

& $Runner -m unittest discover -s tests -v
& $Runner -m PyInstaller --noconfirm --clean Victoria3ModManager.spec

Write-Host "빌드 완료: $ProjectRoot\dist\Victoria3ModManager.exe"
