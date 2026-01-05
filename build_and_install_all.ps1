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

Write-Host "=== 4. Building VSCodeExtension ==="
Set-Location VSCodeExtension\codex-chat
if (!(Test-Path "node_modules")) {
    Write-Host "Running npm install..."
    npm install
}
Write-Host "Running npm run build..."
npm run build

Write-Host "Packaging extension with vsce..."
if (!(Test-Path "node_modules\\.bin\\vsce.cmd")) {
    Write-Host "Installing vsce locally..."
    npm install vsce
}
.\node_modules\.bin\vsce.cmd package

$vsix = Get-ChildItem -Filter *.vsix | Select-Object -First 1
if ($vsix) {
    Write-Host "=== 5. Installing VSIX in VS Code ==="
    code --install-extension $vsix.FullName
} else {
    Write-Host "VSIX package not found! Packaging failed."
}

Set-Location ../..

Write-Host "=== 6. All steps complete! ==="
