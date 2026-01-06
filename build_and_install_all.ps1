# Master build/install script for core, cli, and VSCodeExtension

Write-Host "=== 1. Python venv setup ==="
if (!(Test-Path "venv")) {
    Write-Host "Creating Python venv..."
    python -m venv venv
} else {
    Write-Host "venv already exists."
}

Write-Host "Activating venv..."
& .\venv\Scripts\Activate.ps1

Write-Host "=== 2. Installing Python dependencies ==="
& .\venv\Scripts\python.exe -m pip install --upgrade pip
& .\venv\Scripts\python.exe -m pip install -r requirements.txt


Write-Host "=== 3. Running build.py (if present) ==="
if (Test-Path "build.py") {
    python build.py
} else {
    Write-Host "No build.py found, skipping."
}

Write-Host "=== 3b. Running Python tests (pytest) ==="
$env:PYTHONPATH = "."
if (Test-Path ".\venv\Scripts\pytest.exe") {
    & .\venv\Scripts\pytest.exe tests
} else {
    Write-Host "pytest not found in venv, installing..."
    & .\venv\Scripts\python.exe -m pip install pytest
    & .\venv\Scripts\pytest.exe tests
}

Write-Host "=== 4. Building VSCodeExtension ==="
Set-Location VSCodeExtension\codex-chat

Write-Host "Cleaning node_modules and package-lock.json..."
Remove-Item -Recurse -Force node_modules, package-lock.json -ErrorAction SilentlyContinue

Write-Host "Running npm install..."
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "npm install failed!"
    exit 1
}

Write-Host "Running npm run build..."
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "npm run build failed!"
    exit 1
}

Write-Host "Updating vsce..."
npm install vsce@latest
if ($LASTEXITCODE -ne 0) {
    Write-Host "vsce install failed!"
    exit 1
}

Write-Host "Packaging extension with vsce..."
.\node_modules\.bin\vsce.cmd package
if ($LASTEXITCODE -ne 0) {
    Write-Host "vsce package failed!"
    exit 1
}

$vsix = Get-ChildItem -Filter *.vsix | Select-Object -First 1
if ($vsix) {
    Write-Host "=== 5. Installing VSIX in VS Code ==="
    code --install-extension $vsix.FullName
} else {
    Write-Host "VSIX package not found! Packaging failed."
}

Set-Location ../..

Write-Host "=== 6. All steps complete! ==="
