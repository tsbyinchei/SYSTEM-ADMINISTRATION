#!/usr/bin/env pwsh
# Test SystemCheck.exe

cd d:\V10\dist

Write-Host "🧪 Testing SystemCheck.exe..." -ForegroundColor Yellow
Write-Host "Starting EXE with 5 second timeout..." -ForegroundColor Cyan

# Run EXE and get first output
$process = Start-Process -FilePath ".\SystemCheck.exe" -NoNewWindow -PassThru

# Wait 5 seconds then kill
Start-Sleep 5
try { $process | Stop-Process -Force -ErrorAction SilentlyContinue } catch { }

# Check if log was created
if (Test-Path ".\bot.log") {
    Write-Host "✅ bot.log created!" -ForegroundColor Green
    Write-Host "=== First 30 lines ===" -ForegroundColor Cyan
    Get-Content ".\bot.log" | Select-Object -First 30
} else {
    Write-Host "❌ bot.log NOT created - check for errors" -ForegroundColor Red
}

# Check .env
Write-Host "`n=== .env check ===" -ForegroundColor Cyan
if (Test-Path ".\.env") {
    Write-Host "✅ .env file found" -ForegroundColor Green
    Get-Content ".\.env" | Select-String "API_TOKEN|ADMIN_ID"
} else {
    Write-Host "❌ .env file NOT found!" -ForegroundColor Red
}
