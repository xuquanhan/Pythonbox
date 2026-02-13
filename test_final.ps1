#!/usr/bin/env powershell

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Final Test Script" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Test device detection
$deviceType = "Unknown"
if ($env:COMPUTERNAME -like "*DESKTOP*" -or $env:USERPROFILE -like "*Desktop*") {
    $deviceType = "Desktop"
} elseif ($env:COMPUTERNAME -like "*LAPTOP*" -or $env:USERPROFILE -like "*Laptop*") {
    $deviceType = "Laptop"
}

Write-Host "Device: $deviceType" -ForegroundColor Gray
Write-Host ""

# Test git status
try {
    $status = git status
    Write-Host "Git Status:"
    Write-Host $status
    Write-Host ""
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test git branch
try {
    $branch = git branch -vv
    Write-Host "Git Branch:" 
    Write-Host $branch
    Write-Host ""
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Test completed!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
