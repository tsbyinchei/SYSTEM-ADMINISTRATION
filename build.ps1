# Helper PowerShell build script for V10
# Usage: .\build.ps1 [SystemCheck]
param(
    [string]$Name = "SystemCheck"
)

Write-Host "Preparing build for $Name..."
$ErrorActionPreference = 'Stop'

# Resolve icon absolute path
if (-Not (Test-Path .\icon.ico)) {
    Write-Error "icon.ico not found in project root. Place icon.ico next to this script."
    exit 1
}
$icon = (Resolve-Path .\icon.ico).Path

# Prepare directories
New-Item -ItemType Directory -Path .\build -Force | Out-Null
New-Item -ItemType Directory -Path .\build\temp -Force | Out-Null
New-Item -ItemType Directory -Path .\release -Force | Out-Null

# Copy icon into build folder so spec/workpath relative references work
Copy-Item $icon .\build\icon.ico -Force

# Run PyInstaller (one-line to avoid continuation issues)
Write-Host "Running PyInstaller..."
pyinstaller --onefile --noconsole --uac-admin --icon="$icon" --name=$Name --distpath=.\release --specpath=.\build --workpath=.\build\temp V10.py

# Copy .env to release (if exists)
if (Test-Path .\.env) {
    Copy-Item .\.env .\release\.env -Force
    Write-Host ".env copied to .\release"
} else {
    Write-Host "Warning: .env not found in project root. Remember to copy .env into release after build."
}

Write-Host "Build script finished."