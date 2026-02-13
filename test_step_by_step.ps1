#!/usr/bin/env powershell

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Step-by-Step Test Script" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Test basic variables and device detection
Write-Host "Step 1: Testing device detection..." -ForegroundColor Yellow
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

# Step 2: Test git commands
Write-Host "Step 2: Testing git commands..." -ForegroundColor Yellow
Write-Host ""

# 获取 git 状态信息
try {
    $logOutput = git log --oneline -1
    Write-Host "Latest commit:"
    Write-Host $logOutput
    
    $branchOutput = git branch -vv
    Write-Host ""
    Write-Host "Branch status:"
    Write-Host $branchOutput
    
    $statusOutput = git status -sb
    Write-Host ""
    Write-Host "Status summary:"
    Write-Host $statusOutput
} catch {
    Write-Host "[ERROR] Error getting git info: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Step 3: Test sync status analysis
Write-Host "Step 3: Testing sync status analysis..." -ForegroundColor Yellow
Write-Host ""

# 分析同步状态
$aheadCount = 0
$behindCount = 0
$unstagedCount = 0
$untrackedCount = 0

# 提取 ahead/behind 数量
try {
    if ($branchOutput -match "ahead (\d+)") {
        $aheadCount = $matches[1]
    }
    if ($branchOutput -match "behind (\d+)") {
        $behindCount = $matches[1]
    }
    
    # 提取未暂存和未跟踪文件数量
    if ($statusOutput -match "\d+ modified") {
        $unstagedCount = $matches[0] -replace " modified", ""
    }
    if ($statusOutput -match "\d+ untracked") {
        $untrackedCount = $matches[0] -replace " untracked", ""
    }
} catch {
    Write-Host "[ERROR] Error analyzing sync status: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "[INFO] Sync status analysis:"
Write-Host "- Ahead: $aheadCount"
Write-Host "- Behind: $behindCount"
Write-Host "- Unstaged: $unstagedCount"
Write-Host "- Untracked: $untrackedCount"
Write-Host ""

# Step 4: Test detailed sync status output
Write-Host "Step 4: Testing detailed sync status output..." -ForegroundColor Yellow
Write-Host ""

# 分析同步状态
Write-Host "[STATUS] Detailed Sync Analysis:" -ForegroundColor Cyan
Write-Host "----------------------------------" -ForegroundColor Cyan

if ($aheadCount -eq 0 -and $behindCount -eq 0 -and $unstagedCount -eq 0 -and $untrackedCount -eq 0) {
    Write-Host "[GITHUB] GitHub: Fully synchronized" -ForegroundColor Green
    Write-Host "[Device] $($deviceType): Fully synchronized" -ForegroundColor Green
    Write-Host "[OVERALL] All devices: Completely synchronized" -ForegroundColor Green
    Write-Host "[INFO]    No pending changes or commits" -ForegroundColor Gray
} else {
    $syncIssues = @()
    
    if ($aheadCount -gt 0) {
        Write-Host "[GITHUB] GitHub: Partially synchronized" -ForegroundColor Yellow
        Write-Host "[Device] $($deviceType): Has latest changes" -ForegroundColor Green
        Write-Host "[LOCAL]  Local commits: $aheadCount commit(s) ready to push" -ForegroundColor Yellow
        $syncIssues += "$aheadCount commit(s) not pushed to GitHub"
    } elseif ($behindCount -gt 0) {
        Write-Host "[GITHUB] GitHub: Has latest changes" -ForegroundColor Green
        Write-Host "[Device] $($deviceType): Partially synchronized" -ForegroundColor Yellow
        Write-Host "[REMOTE] Remote commits: $behindCount commit(s) ready to pull" -ForegroundColor Yellow
        $syncIssues += "$behindCount commit(s) not pulled from GitHub"
    } else {
        Write-Host "[GITHUB] GitHub: Synchronized" -ForegroundColor Green
        Write-Host "[Device] $($deviceType): Partially synchronized" -ForegroundColor Yellow
        
        if ($unstagedCount -gt 0) {
            Write-Host "[FILES]  Unstaged files: $unstagedCount file(s) need staging" -ForegroundColor Yellow
            $syncIssues += "$unstagedCount unstaged file(s)"
        }
        if ($untrackedCount -gt 0) {
            Write-Host "[FILES]  Untracked files: $untrackedCount file(s) need tracking" -ForegroundColor Yellow
            $syncIssues += "$untrackedCount untracked file(s)"
        }
    }
    
    if ($syncIssues.Count -gt 0) {
        Write-Host "[OVERALL] Sync status: Partially synchronized" -ForegroundColor Yellow
        Write-Host "[ISSUES]  Pending synchronization issues:" -ForegroundColor Red
        foreach ($issue in $syncIssues) {
            Write-Host "          - $issue" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Script completed!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
