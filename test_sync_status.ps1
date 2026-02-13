#!/usr/bin/env powershell

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Test Sync Status Script" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 检测当前设备类型
$deviceType = "Unknown"
if ($env:COMPUTERNAME -like "*DESKTOP*" -or $env:USERPROFILE -like "*Desktop*") {
    $deviceType = "Desktop"
} elseif ($env:COMPUTERNAME -like "*LAPTOP*" -or $env:USERPROFILE -like "*Laptop*") {
    $deviceType = "Laptop"
}

Write-Host "[DEVICE] Current device: $deviceType" -ForegroundColor Gray
Write-Host ""

# 测试 git 命令
Write-Host "Testing git commands..." -ForegroundColor Yellow
Write-Host ""

try {
    $logOutput = git log --oneline -1
    Write-Host "Latest commit:"
    Write-Host $logOutput
    Write-Host ""
    
    $branchOutput = git branch -vv
    Write-Host "Branch status:"
    Write-Host $branchOutput
    Write-Host ""
    
    $statusOutput = git status -sb
    Write-Host "Status summary:"
    Write-Host $statusOutput
    Write-Host ""
    
    # 提取 ahead/behind 数量
    $aheadCount = 0
    $behindCount = 0
    
    if ($branchOutput -match "ahead (\d+)") {
        $aheadCount = $matches[1]
    }
    if ($branchOutput -match "behind (\d+)") {
        $behindCount = $matches[1]
    }
    
    Write-Host "Ahead count: $aheadCount" -ForegroundColor Cyan
    Write-Host "Behind count: $behindCount" -ForegroundColor Cyan
    
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Test completed!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
