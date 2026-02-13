#!/usr/bin/env powershell

Write-Host "Hello, World!" -ForegroundColor Green
Write-Host "Testing basic PowerShell script..." -ForegroundColor Cyan

# Check Git status
try {
    $statusOutput = git status
    Write-Host "Git status:"
    Write-Host $statusOutput
} catch {
    Write-Host "Error checking Git status: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Script completed!" -ForegroundColor Green
